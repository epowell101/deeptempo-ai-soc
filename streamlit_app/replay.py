#!/usr/bin/env python3
"""
Scenario Replay Module

Provides replay capabilities for attack scenarios:
- Instant load: Load all data at once
- Accelerated replay: Play 16 hours in configurable time
- Real-time simulation: For live demos

Also supports loading custom scenarios.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"
SCENARIOS_DIR = DATA_DIR / "scenarios"


class ScenarioManager:
    """Manages scenario loading and listing."""
    
    @staticmethod
    def list_scenarios() -> List[Dict]:
        """List all available scenarios."""
        scenarios = []
        
        for scenario_dir in SCENARIOS_DIR.iterdir():
            if scenario_dir.is_dir():
                manifest_file = scenario_dir / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    manifest["path"] = str(scenario_dir)
                    manifest["id"] = scenario_dir.name
                    scenarios.append(manifest)
        
        return scenarios
    
    @staticmethod
    def load_scenario(scenario_id: str) -> Dict:
        """Load a complete scenario."""
        scenario_dir = SCENARIOS_DIR / scenario_id
        
        if not scenario_dir.exists():
            raise ValueError(f"Scenario {scenario_id} not found")
        
        data = {"id": scenario_id}
        
        # Load manifest
        manifest_file = scenario_dir / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file) as f:
                data["manifest"] = json.load(f)
        
        # Load ground truth
        gt_file = scenario_dir / "ground_truth.json"
        if gt_file.exists():
            with open(gt_file) as f:
                data["ground_truth"] = json.load(f)
        
        # Load raw logs
        conn_file = scenario_dir / "raw_logs" / "zeek_conn.json"
        if conn_file.exists():
            with open(conn_file) as f:
                data["conn_logs"] = json.load(f)
        
        dns_file = scenario_dir / "raw_logs" / "zeek_dns.json"
        if dns_file.exists():
            with open(dns_file) as f:
                data["dns_logs"] = json.load(f)
        
        # Load rules output
        alerts_file = scenario_dir / "rules_output" / "alerts.json"
        if alerts_file.exists():
            with open(alerts_file) as f:
                data["alerts"] = json.load(f)
        
        # Load LogLM output
        findings_file = scenario_dir / "loglm_output" / "findings.json"
        if findings_file.exists():
            with open(findings_file) as f:
                data["findings"] = json.load(f)
        
        incidents_file = scenario_dir / "loglm_output" / "incidents.json"
        if incidents_file.exists():
            with open(incidents_file) as f:
                data["incidents"] = json.load(f)
        
        # Load evaluation
        eval_file = scenario_dir / "evaluation_results.json"
        if eval_file.exists():
            with open(eval_file) as f:
                data["evaluation"] = json.load(f)
        
        return data


class ReplayEngine:
    """
    Replay engine for scenario playback.
    
    Supports:
    - Instant mode: All events available immediately
    - Accelerated mode: Events released over compressed time
    - Real-time mode: Events released at actual timestamps
    """
    
    def __init__(self, scenario_data: Dict):
        self.scenario = scenario_data
        self.mode = "instant"
        self.speed = 1.0  # Multiplier for accelerated mode
        self.current_time = None
        self.start_time = None
        self.is_playing = False
        self._thread = None
        self._callbacks = []
        
        # Parse all events with timestamps
        self.all_events = self._parse_events()
        self.visible_events = []
        self.visible_alerts = []
        self.visible_findings = []
    
    def _parse_events(self) -> List[Dict]:
        """Parse and sort all events by timestamp."""
        events = []
        
        # Add connection logs
        for log in self.scenario.get("conn_logs", []):
            events.append({
                "type": "conn",
                "timestamp": datetime.fromisoformat(log["ts"]),
                "data": log
            })
        
        # Add DNS logs
        for log in self.scenario.get("dns_logs", []):
            events.append({
                "type": "dns",
                "timestamp": datetime.fromisoformat(log["ts"]),
                "data": log
            })
        
        # Sort by timestamp
        events.sort(key=lambda x: x["timestamp"])
        
        return events
    
    def set_mode(self, mode: str, speed: float = 1.0):
        """Set replay mode."""
        self.mode = mode
        self.speed = speed
        
        if mode == "instant":
            # All events visible immediately
            self.visible_events = self.all_events.copy()
            self._update_detections()
    
    def _update_detections(self):
        """Update visible alerts and findings based on visible events."""
        visible_event_ids = {e["data"]["id"] for e in self.visible_events}
        
        # Filter alerts
        self.visible_alerts = [
            a for a in self.scenario.get("alerts", [])
            if a.get("event_id") in visible_event_ids
        ]
        
        # Filter findings
        self.visible_findings = [
            f for f in self.scenario.get("findings", [])
            if any(eid in visible_event_ids for eid in f.get("event_ids", []))
        ]
    
    def start_replay(self, duration_seconds: float = 300):
        """Start accelerated replay."""
        if self.is_playing:
            return
        
        self.is_playing = True
        self.visible_events = []
        self.start_time = datetime.now()
        
        if not self.all_events:
            return
        
        # Calculate time range
        first_event_time = self.all_events[0]["timestamp"]
        last_event_time = self.all_events[-1]["timestamp"]
        scenario_duration = (last_event_time - first_event_time).total_seconds()
        
        # Calculate speed multiplier
        self.speed = scenario_duration / duration_seconds
        
        self._thread = threading.Thread(target=self._replay_loop)
        self._thread.daemon = True
        self._thread.start()
    
    def _replay_loop(self):
        """Background thread for replay."""
        if not self.all_events:
            return
        
        first_event_time = self.all_events[0]["timestamp"]
        
        for event in self.all_events:
            if not self.is_playing:
                break
            
            # Calculate when this event should appear
            event_offset = (event["timestamp"] - first_event_time).total_seconds()
            target_real_time = event_offset / self.speed
            
            # Wait until it's time
            elapsed = (datetime.now() - self.start_time).total_seconds()
            wait_time = target_real_time - elapsed
            
            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))  # Check every 100ms
                continue
            
            # Add event
            self.visible_events.append(event)
            self._update_detections()
            
            # Notify callbacks
            for callback in self._callbacks:
                callback(event)
        
        self.is_playing = False
    
    def stop_replay(self):
        """Stop replay."""
        self.is_playing = False
        if self._thread:
            self._thread.join(timeout=1)
    
    def add_callback(self, callback: Callable):
        """Add callback for new events."""
        self._callbacks.append(callback)
    
    def get_progress(self) -> float:
        """Get replay progress (0-1)."""
        if not self.all_events:
            return 1.0
        return len(self.visible_events) / len(self.all_events)
    
    def get_stats(self) -> Dict:
        """Get current replay statistics."""
        return {
            "total_events": len(self.all_events),
            "visible_events": len(self.visible_events),
            "visible_alerts": len(self.visible_alerts),
            "visible_findings": len(self.visible_findings),
            "progress": self.get_progress(),
            "is_playing": self.is_playing
        }


def render_scenario_selector():
    """Render scenario selection UI."""
    st.subheader("📂 Scenario Selection")
    
    scenarios = ScenarioManager.list_scenarios()
    
    if not scenarios:
        st.warning("No scenarios found. Generate one with:")
        st.code("python scripts/generate_scenario.py", language="bash")
        return None
    
    # Create selection options
    options = {s["id"]: f"{s['name']} ({s['total_events']:,} events)" for s in scenarios}
    
    selected_id = st.selectbox(
        "Select Scenario",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    
    # Show scenario details
    selected = next((s for s in scenarios if s["id"] == selected_id), None)
    if selected:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Events", f"{selected['total_events']:,}")
        with col2:
            st.metric("Malicious", selected.get("malicious_events", "N/A"))
        with col3:
            st.metric("Duration", f"{selected.get('duration_hours', 'N/A')} hrs")
        
        st.markdown(f"**Description:** {selected.get('description', 'N/A')}")
    
    return selected_id


def render_replay_controls(engine: ReplayEngine):
    """Render replay control UI."""
    st.subheader("▶️ Replay Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mode = st.radio(
            "Replay Mode",
            ["Instant", "Accelerated (5 min)", "Accelerated (1 min)"],
            horizontal=True
        )
    
    with col2:
        if mode == "Instant":
            if st.button("Load All Events"):
                engine.set_mode("instant")
                st.success("All events loaded!")
        else:
            duration = 300 if "5 min" in mode else 60
            if st.button("Start Replay"):
                engine.start_replay(duration_seconds=duration)
                st.info(f"Replay started ({duration}s)")
            
            if engine.is_playing:
                if st.button("Stop Replay"):
                    engine.stop_replay()
    
    # Progress
    stats = engine.get_stats()
    st.progress(stats["progress"])
    st.caption(f"{stats['visible_events']:,} / {stats['total_events']:,} events | "
               f"{stats['visible_alerts']} alerts | {stats['visible_findings']} findings")


def create_custom_scenario_template():
    """Create a template for custom scenarios."""
    template = {
        "name": "Custom Attack Scenario",
        "description": "Description of your attack scenario",
        "log_types": ["zeek_conn", "zeek_dns"],
        "duration_hours": 1,
        "total_events": 0,
        "malicious_events": 0,
        "benign_events": 0,
        "created": datetime.now().isoformat(),
        "author": "Your Name"
    }
    
    return json.dumps(template, indent=2)


def render_custom_scenario_upload():
    """Render UI for uploading custom scenarios."""
    st.subheader("📤 Upload Custom Scenario")
    
    st.markdown("""
    Upload your own scenario data to compare detection methods.
    
    **Required files:**
    - `manifest.json` - Scenario metadata
    - `raw_logs/zeek_conn.json` - Connection logs
    - `raw_logs/zeek_dns.json` - DNS logs (optional)
    - `ground_truth.json` - Labels for evaluation
    """)
    
    with st.expander("View manifest.json template"):
        st.code(create_custom_scenario_template(), language="json")
    
    uploaded_files = st.file_uploader(
        "Upload scenario files",
        accept_multiple_files=True,
        type=["json"]
    )
    
    scenario_name = st.text_input("Scenario Name", "my_custom_scenario")
    
    if uploaded_files and st.button("Create Scenario"):
        scenario_dir = SCENARIOS_DIR / "custom" / scenario_name
        scenario_dir.mkdir(parents=True, exist_ok=True)
        (scenario_dir / "raw_logs").mkdir(exist_ok=True)
        (scenario_dir / "rules_output").mkdir(exist_ok=True)
        (scenario_dir / "loglm_output").mkdir(exist_ok=True)
        
        for uploaded_file in uploaded_files:
            # Determine destination
            filename = uploaded_file.name
            if "conn" in filename.lower():
                dest = scenario_dir / "raw_logs" / "zeek_conn.json"
            elif "dns" in filename.lower():
                dest = scenario_dir / "raw_logs" / "zeek_dns.json"
            elif "manifest" in filename.lower():
                dest = scenario_dir / "manifest.json"
            elif "ground_truth" in filename.lower():
                dest = scenario_dir / "ground_truth.json"
            else:
                dest = scenario_dir / filename
            
            with open(dest, "wb") as f:
                f.write(uploaded_file.getvalue())
        
        st.success(f"Scenario '{scenario_name}' created! Run detection pipelines:")
        st.code(f"""
python scripts/rules_detection.py --scenario custom/{scenario_name}
python scripts/loglm_detection.py --scenario custom/{scenario_name}
python scripts/evaluate.py --scenario custom/{scenario_name}
        """, language="bash")
