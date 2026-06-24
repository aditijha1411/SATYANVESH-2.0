from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from collections import defaultdict
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.event import Event
from models.entity import Entity

class TimelineEngine:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = uuid.UUID(case_id)

    def get_full_timeline(self) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id
        ).all()
        formatted = self._format_events(events)
        formatted = self._enrich_events(formatted)
        return sorted(formatted, key=lambda x: x["timestamp"] or "")

    def get_entity_timeline(self, entity_value: str) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id
        ).filter(
            (Event.source_entity == entity_value) | (Event.target_entity == entity_value)
        ).all()
        formatted = self._format_events(events)
        formatted = self._enrich_events(formatted)
        return sorted(formatted, key=lambda x: x["timestamp"] or "")

    def get_timeline_between(self, start: str, end: str) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.timestamp >= start,
            Event.timestamp <= end
        ).all()
        formatted = self._format_events(events)
        return sorted(formatted, key=lambda x: x["timestamp"] or "")

    def get_multi_entity_timeline(self, entities: List[str]) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.source_entity.in_(entities) | Event.target_entity.in_(entities)
        ).all()
        formatted = self._format_events(events)
        formatted = self._enrich_events(formatted)
        return sorted(formatted, key=lambda x: x["timestamp"] or "")

    def detect_suspicious_patterns(self) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id
        ).all()
        formatted = self._format_events(events)
        sorted_events = sorted(formatted, key=lambda x: x["timestamp"] or "")

        patterns = []
        patterns += self._detect_burst_activity(sorted_events)
        patterns += self._detect_late_night_activity(sorted_events)
        patterns += self._detect_repeated_contact(sorted_events)
        patterns += self._detect_call_then_movement(sorted_events)
        patterns += self._detect_one_time_contacts(sorted_events)
        patterns += self._detect_long_stationary(sorted_events)
        patterns += self._detect_activity_gap(sorted_events)

        return sorted(patterns, key=lambda x: x["severity"], reverse=True)

    def _detect_burst_activity(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        hour_buckets = defaultdict(list)
        for event in events:
            if event["timestamp"] and len(event["timestamp"]) >= 13:
                bucket = event["timestamp"][:13]
                hour_buckets[bucket].append(event)

        for hour, evts in hour_buckets.items():
            if len(evts) >= 5:
                entities = list(set([e["source"] for e in evts if e["source"]]))
                patterns.append({
                    "pattern_type": "BURST_ACTIVITY",
                    "severity": 8,
                    "description": f"{len(evts)} events detected within a single hour at {hour}:00. "
                                   f"Entities involved: {', '.join(entities[:3])}. "
                                   f"Sudden surge in activity may indicate coordination before or after a critical event.",
                    "what_this_means": "Burst of activity in one hour — possible pre-crime coordination or panic communication.",
                    "recommended_action": "Review all events in this hour closely. Cross-reference with crime scene TOD.",
                    "entities": entities,
                    "timestamp": hour + ":00:00",
                    "event_count": len(evts)
                })
        return patterns

    def _detect_late_night_activity(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        night_events = [
            e for e in events
            if e["timestamp"] and len(e["timestamp"]) >= 13
            and e["timestamp"][11:13] in ["00", "01", "02", "03", "04"]
        ]
        if len(night_events) >= 3:
            entities = list(set([e["source"] for e in night_events if e["source"]]))
            patterns.append({
                "pattern_type": "LATE_NIGHT_ACTIVITY",
                "severity": 7,
                "description": f"{len(night_events)} events detected between midnight and 5am. "
                               f"Entities: {', '.join(entities[:3])}. "
                               f"Late night activity is statistically unusual and warrants investigation.",
                "what_this_means": "Activity during unusual hours — suspect may have been at crime scene overnight.",
                "recommended_action": "Map late night events against victim TODs. Check GPS for overnight stationary periods.",
                "entities": entities,
                "timestamp": night_events[0]["timestamp"],
                "event_count": len(night_events)
            })
        return patterns

    def _detect_repeated_contact(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        contact_count = defaultdict(int)
        contact_events = defaultdict(list)
        for event in events:
            if event["source"] and event["target"] and event["event_type"] in [
                "PHONE_CALL", "SMS", "WHATSAPP_MESSAGE", "WHATSAPP_CALL"
            ]:
                key = tuple(sorted([event["source"], event["target"]]))
                contact_count[key] += 1
                contact_events[key].append(event["timestamp"])

        for (a, b), count in contact_count.items():
            if count >= 5:
                patterns.append({
                    "pattern_type": "REPEATED_CONTACT",
                    "severity": 9,
                    "description": f"{a} and {b} contacted each other {count} times. "
                                   f"First contact: {contact_events[(a,b)][0]}. "
                                   f"Last contact: {contact_events[(a,b)][-1]}. "
                                   f"High frequency contact strongly suggests relationship or coordination.",
                    "what_this_means": f"These two numbers have significant contact history — {count} interactions detected.",
                    "recommended_action": f"Obtain full content of communications between {a} and {b}. Map contact timing against crime dates.",
                    "entities": [a, b],
                    "timestamp": contact_events[(a,b)][0],
                    "event_count": count
                })
        return patterns

    def _detect_call_then_movement(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        call_events = [e for e in events if e["event_type"] in ["PHONE_CALL", "WHATSAPP_CALL"]]
        gps_events = [e for e in events if e["event_type"] == "GPS_MOVEMENT"]

        for call in call_events:
            if not call["timestamp"] or len(call["timestamp"]) < 13:
                continue
            call_hour = call["timestamp"][:13]
            matching_gps = [
                g for g in gps_events
                if g["source"] == call["source"]
                and g["timestamp"]
                and g["timestamp"][:13] == call_hour
            ]
            if matching_gps:
                patterns.append({
                    "pattern_type": "CALL_BEFORE_MOVEMENT",
                    "severity": 7,
                    "description": f"{call['source']} made a call at {call['timestamp']} "
                                   f"and was detected moving at {matching_gps[0]['location']} in the same hour. "
                                   f"Call followed by immediate movement is a coordination indicator.",
                    "what_this_means": "Entity made a call then immediately moved — possible coordination or fleeing behaviour.",
                    "recommended_action": f"Obtain call content for {call['source']} at {call['timestamp']}. Compare movement destination with crime scene.",
                    "entities": [call["source"]],
                    "timestamp": call["timestamp"],
                    "event_count": 1
                })
        return patterns[:3]

    def _detect_one_time_contacts(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        contact_count = defaultdict(int)
        contact_info = {}
        for event in events:
            if event["source"] and event["event_type"] in ["PHONE_CALL", "SMS"]:
                contact_count[event["source"]] += 1
                contact_info[event["source"]] = event

        for entity, count in contact_count.items():
            if count == 1:
                evt = contact_info[entity]
                patterns.append({
                    "pattern_type": "ONE_TIME_CONTACT",
                    "severity": 6,
                    "description": f"{entity} appears only once in records at {evt['timestamp']}. "
                                   f"Single-use contacts are typical of burner phones or one-time coordination numbers.",
                    "what_this_means": "This number appears only once — possible burner phone or disposable SIM.",
                    "recommended_action": f"Investigate {entity} further. Check if this number appears in any other case records. Try tower dump for this number.",
                    "entities": [entity],
                    "timestamp": evt["timestamp"],
                    "event_count": 1
                })
        return patterns[:5]

    def _detect_long_stationary(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        gps_events = sorted(
            [e for e in events if e["event_type"] == "GPS_MOVEMENT" and e["timestamp"]],
            key=lambda x: x["timestamp"]
        )
        entity_gps = defaultdict(list)
        for e in gps_events:
            if e["source"]:
                entity_gps[e["source"]].append(e)

        for entity, gps_list in entity_gps.items():
            for i in range(len(gps_list) - 1):
                e1 = gps_list[i]
                e2 = gps_list[i + 1]
                if e1["location"] == e2["location"]:
                    try:
                        t1 = e1["timestamp"]
                        t2 = e2["timestamp"]
                        h1 = int(t1[11:13])
                        h2 = int(t2[11:13])
                        diff = h2 - h1 if h2 >= h1 else (24 - h1 + h2)
                        if diff >= 4:
                            patterns.append({
                                "pattern_type": "LONG_STATIONARY_PERIOD",
                                "severity": 9,
                                "description": f"{entity} was stationary at '{e1['location']}' "
                                               f"from {t1} to {t2} — approximately {diff} hours. "
                                               f"Extended stationary periods at a location strongly correlate with crime scene presence.",
                                "what_this_means": f"Suspect stayed at same location for {diff}+ hours — possible overnight crime scene presence.",
                                "recommended_action": f"Cross-reference this location and time window with victim address and TOD. This is critical evidence.",
                                "entities": [entity],
                                "timestamp": t1,
                                "event_count": diff
                            })
                    except:
                        pass
        return patterns

    def _detect_activity_gap(self, events: List[Dict]) -> List[Dict]:
        patterns = []
        entity_events = defaultdict(list)
        for e in events:
            if e["source"] and e["timestamp"]:
                entity_events[e["source"]].append(e["timestamp"])

        for entity, timestamps in entity_events.items():
            sorted_ts = sorted(timestamps)
            for i in range(len(sorted_ts) - 1):
                t1 = sorted_ts[i]
                t2 = sorted_ts[i + 1]
                try:
                    if len(t1) >= 13 and len(t2) >= 13:
                        d1 = t1[:10]
                        d2 = t2[:10]
                        if d1 != d2:
                            from datetime import datetime
                            dt1 = datetime.strptime(d1, "%Y-%m-%d")
                            dt2 = datetime.strptime(d2, "%Y-%m-%d")
                            gap_days = (dt2 - dt1).days
                            if gap_days >= 5:
                                patterns.append({
                                    "pattern_type": "ACTIVITY_GAP",
                                    "severity": 5,
                                    "description": f"{entity} shows a {gap_days}-day gap in activity "
                                                   f"between {d1} and {d2}. "
                                                   f"Sudden disappearance from records may indicate SIM change, travel, or deliberate avoidance.",
                                    "what_this_means": f"No activity for {gap_days} days — possible SIM change, city change, or deliberate digital silence.",
                                    "recommended_action": f"Check if {entity} obtained a new SIM during this period. Check travel records.",
                                    "entities": [entity],
                                    "timestamp": t1,
                                    "event_count": gap_days
                                })
                except:
                    pass
        return patterns[:3]

    def _format_events(self, events: List) -> List[Dict]:
        formatted = []
        for e in events:
            formatted.append({
                "id": str(e.id),
                "event_type": e.event_type,
                "timestamp": e.timestamp,
                "source": e.source_entity,
                "target": e.target_entity,
                "direction": e.direction,
                "duration_seconds": e.duration_seconds,
                "location": e.location,
                "cell_id": e.cell_id,
                "imei": e.imei,
                "summary": self._generate_summary(e)
            })
        return formatted

    def _generate_summary(self, event) -> str:
        t = event.event_type
        src = event.source_entity or "Unknown"
        tgt = event.target_entity or "Unknown"
        dur = event.duration_seconds or 0
        loc = event.location or ""

        if t == "PHONE_CALL":
            dir_text = "called" if event.direction in ["MO", "OUTGOING"] else "received call from"
            return f"{src} {dir_text} {tgt} ({dur}s){' at ' + loc if loc else ''}"
        elif t == "SMS":
            return f"{src} sent SMS to {tgt}{' at ' + loc if loc else ''}"
        elif t == "GPS_MOVEMENT":
            return f"{src} detected at {loc or tgt}"
        elif t == "INTERNET_SESSION":
            return f"{src} accessed {tgt} ({dur}s)"
        elif t == "WEBSITE_VISIT":
            return f"{src} visited {tgt}"
        elif t == "FINANCIAL_TRANSACTION":
            return f"{src} made transaction to {tgt}"
        elif t == "WHATSAPP_MESSAGE":
            return f"{src} sent WhatsApp message to {tgt}"
        elif t == "WHATSAPP_CALL":
            return f"{src} made WhatsApp call to {tgt} ({dur}s)"
        elif t == "BLUETOOTH_PAIRING":
            return f"Device {src} paired with {tgt}{' at ' + loc if loc else ''}"
        elif t == "IOT_ACTIVITY":
            return f"IoT device {src} recorded event at {loc}"
        else:
            return f"{t}: {src} → {tgt}"

    def _enrich_events(self, events: List[Dict]) -> List[Dict]:
        for event in events:
            ts = event.get("timestamp", "")
            if ts and len(ts) >= 13:
                hour = int(ts[11:13])
                if 0 <= hour < 5:
                    event["time_flag"] = "LATE_NIGHT"
                elif 5 <= hour < 9:
                    event["time_flag"] = "EARLY_MORNING"
                elif 22 <= hour <= 23:
                    event["time_flag"] = "NIGHT"
                else:
                    event["time_flag"] = "NORMAL"
            else:
                event["time_flag"] = "UNKNOWN"
        return events