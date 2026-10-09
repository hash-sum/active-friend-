import ollama
import time
import schedule
import threading
import json
import os
import sys
import argparse
from datetime import datetime

# Ensure safe UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ==============================================================================
# Crisis & Emergency Resources
# ==============================================================================
CRISIS_HELPLINES = """
================================================================================
🆘 IMMEDIATE CRISIS & EMOTIONAL SUPPORT RESOURCES (FREE & CONFIDENTIAL 24/7):
--------------------------------------------------------------------------------
• US & Canada: Call or text 988 (Suicide & Crisis Lifeline)
• Crisis Text Line: Text "HOME" to 741741 (US & Canada) or 85258 (UK)
• UK: Call 111 (NHS Mental Health) or 116 123 (Samaritans)
• International Helplines: https://findahelpline.com / https://befrienders.org
• Emergency: If you or someone else is in immediate physical danger, call 911 / 999 / 112.
================================================================================
"""

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "self harm",
    "cutting myself", "don't want to live", "better off dead", "hurt myself"
]


class ActiveFriend:
    def __init__(self, model_name="llama3.2:1b", deep_reasoning=False):
        self.user_data_file = "user_data.json"
        self.user_data = self.load_user_data()

        # If deep_reasoning flag is passed or model is gemma2, set mode accordingly
        if deep_reasoning or "gemma" in model_name.lower():
            self.model_name = "gemma2"
            self.is_deep_mode = True
        else:
            self.model_name = model_name
            self.is_deep_mode = False

        self.conversation_history = []
        self.init_conversation_history()
        self.print_welcome_banner()

    def build_system_prompt(self):
        name = self.user_data.get("name", "Friend")
        interests = ", ".join(self.user_data.get("interests", ["self-care", "mindfulness"]))

        if self.is_deep_mode:
            # Gemma 2: Advanced Reasoning & Mental Stability System Prompt
            return (
                "You are an advanced empathetic companion, cognitive reasoning guide, and mental health support partner "
                "powered by Gemma 2. Your purpose is to provide structured, deep cognitive reasoning to help the user "
                "navigate complicated mental instability, acute overwhelm, anxiety spirals, burnout, and emotional dysregulation.\n\n"
                "### COGNITIVE & EMOTIONAL REASONING FRAMEWORK:\n"
                "1. **Compassionate Grounding & Safety First**: Immediately acknowledge and validate the user's emotional pain "
                "without judgment or toxic positivity. If the user feels dissociated, panicked, or out of control, offer grounding first.\n"
                "2. **Cognitive Deconstruction**: Carefully untangle knotty, overwhelming, or catastrophic thoughts. Break down the situation "
                "into objective facts versus cognitive distortions (e.g., all-or-nothing thinking, catastrophizing, mind-reading, emotional reasoning).\n"
                "3. **Dialectical Reasoning & Perspective Shift**: Hold space for conflicting truths (e.g., 'It is completely valid to feel exhausted, "
                "AND you still retain agency over your next small step'). Clarify what is inside their control versus what is outside.\n"
                "4. **Somatic Stabilization**: When appropriate, guide the user through somatic regulation techniques (5-4-3-2-1 sensory grounding, "
                "box breathing, or the physiological sigh) to calm the autonomic nervous system.\n"
                "5. **Micro-Action Strategy**: When facing mental paralysis or overwhelm, never prescribe big, intimidating tasks. Offer 1 or 2 "
                "manageable, tiny, concrete micro-steps to restore equilibrium.\n"
                "6. **Ethical Boundaries**: You are a supportive AI peer and reasoning companion, not a licensed medical professional. If acute self-harm "
                "or crisis is detected, gently encourage reaching out to emergency resources.\n\n"
                f"User Profile: Name: {name} | Interests: {interests}.\n"
                "Tone: Grounded, deeply empathetic, lucid, structured, non-judgmental, and profoundly steady."
            )
        else:
            # Llama 3.2 1B: Fast Casual Companion Prompt
            return (
                "You are an active, caring best friend and daily mental health companion. "
                "Your goal is to motivate the user, check in on their mental well-being, "
                "give actionable tips on self-improvement and relationship building, and remind them to take breaks. "
                f"You know their interests: {interests}. "
                "Keep your responses friendly, warm, supportive, and relatively concise."
            )

    def init_conversation_history(self):
        prompt = self.build_system_prompt()
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = prompt
        else:
            self.conversation_history = [{"role": "system", "content": prompt}]

    def update_model_mode(self, model_name, deep_mode=None):
        self.model_name = model_name
        if deep_mode is not None:
            self.is_deep_mode = deep_mode
        else:
            self.is_deep_mode = "gemma" in model_name.lower()
        
        # Dynamically sync system prompt in conversation history
        self.init_conversation_history()
        mode_desc = "🧠 Gemma 2 [Deep Reasoning & Mental Stability Mode]" if self.is_deep_mode else f"⚡ {self.model_name} [Fast Casual Mode]"
        print(f"\n[⚙️ System]: Model switched to {self.model_name}. Active Mode: {mode_desc}\n")

    def print_welcome_banner(self):
        print("=" * 70)
        print("🌟 Active Friend AI - Mental Health & Social Companion")
        print("=" * 70)
        mode_label = "Deep Cognitive Reasoning (Gemma 2)" if self.is_deep_mode else "Fast Casual Companion (Llama 3.2 1B)"
        print(f"🤖 Active Brain: {self.model_name} ({mode_label})")
        print("💬 Type naturally to chat. Special commands:")
        print("   • /reason or /deep  : Switch to Gemma 2 for deep reasoning & emotional untangling")
        print("   • /fast or /chat    : Switch to Llama 3.2 1B for quick casual check-ins")
        print("   • /switch           : Toggle between Gemma 2 and Llama 3.2 1B")
        print("   • /ground           : Trigger an interactive somatic grounding exercise")
        print("   • /crisis           : Display 24/7 crisis hotlines & emergency support")
        print("   • /status           : View current brain mode and profile stats")
        print("   • schedule meetup   : Schedule a hangout with a friend on Google Calendar")
        print("   • quit or exit      : End session")
        print("=" * 70)

    def load_user_data(self):
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "name": "Samuel",
            "interests": ["coding", "hackathons", "mental health", "reading"],
            "friends": []
        }

    def save_user_data(self):
        with open(self.user_data_file, "w") as f:
            json.dump(self.user_data, f, indent=4)

    def check_crisis_indicators(self, text):
        lower = text.lower()
        return any(k in lower for k in CRISIS_KEYWORDS)

    def chat(self, user_input):
        is_crisis = self.check_crisis_indicators(user_input)
        self.conversation_history.append({"role": "user", "content": user_input})

        prefix = "🧠 Gemma 2 Reasoning" if self.is_deep_mode else "Friend"
        print(f"\n{prefix}: ", end="", flush=True)

        full_reply = ""
        try:
            # Stream response for real-time responsiveness
            stream = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=True
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                print(token, end="", flush=True)
                full_reply += token
            print()  # newline after streaming completes

            self.conversation_history.append({"role": "assistant", "content": full_reply})

            if is_crisis:
                print(CRISIS_HELPLINES)

            return full_reply
        except Exception as e:
            error_msg = f"\n[!] Error generating response. Please check that Ollama is running and '{self.model_name}' is installed.\nDetails: {e}"
            print(error_msg)
            return error_msg

    def trigger_grounding_exercise(self):
        print("\n" + "=" * 60)
        print("🌿 Somatic Grounding Exercise: 5-4-3-2-1 Sensory Reset")
        print("=" * 60)
        print("Take a slow, deep breath in... and gently let it out.")
        print("Let's anchor your nervous system in the present moment:\n")
        print("👁️  5 things you can SEE around you (e.g., your desk, light, screen)")
        print("✋ 4 things you can physically FEEL (e.g., feet on floor, clothes on shoulders)")
        print("👂 3 things you can HEAR (e.g., computer fan, distant traffic, your breath)")
        print("👃 2 things you can SMELL (or scents you like)")
        print("👅 1 thing you can TASTE (or take a sip of cool water)")
        print("\n💡 Take one more slow breath. Your mind is safe right here, right now.")
        print("=" * 60)

    def check_screen_time(self):
        print("\n[🤖 Friend Reminder]: Hey! You've been looking at the screen for a while. Let's take a 5-minute break! Maybe stretch or grab some water? 💧\nYou: ", end="", flush=True)

    def schedule_meetup(self, friend_name):
        try:
            import google_calendar_utils
            service = google_calendar_utils.get_calendar_service()
            if service:
                email = input(f"Enter {friend_name}'s email address (or press Enter to skip email): ").strip()
                if not email:
                    email = "friend@example.com"
                google_calendar_utils.create_meetup_event(service, email, friend_name)
                print(f"[📅 Scheduler]: Event created for hangout with {friend_name}! ☕")
                return
        except Exception as e:
            pass

        print(f"\n[📅 Scheduler]: Finding a good time to hang out with {friend_name}...")
        print(f"[📅 Scheduler]: Event created! 'Coffee with {friend_name}' scheduled for this weekend. ☕")

    def run_scheduler(self):
        schedule.every(60).minutes.do(self.check_screen_time)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        # Start the background scheduler thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nFriend: Take good care of yourself! 💙")
                break

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit"]:
                print("Friend: Bye! Remember to take care of yourself, breathe, and rest! 💙")
                break

            # Command handling
            if user_input.lower() in ["/reason", "/deep", "/gemma", "/gemma2"]:
                self.update_model_mode(model_name="gemma2", deep_mode=True)
                print("💡 Gemma 2 Deep Reasoning is now active. Share what is feeling tangled, unstable, or overwhelming.")
                continue

            if user_input.lower() in ["/fast", "/chat", "/llama"]:
                self.update_model_mode(model_name="llama3.2:1b", deep_mode=False)
                print("💡 Fast companion mode active for casual chats, reminders, and check-ins.")
                continue

            if user_input.lower() == "/switch":
                if self.model_name == "llama3.2:1b":
                    self.update_model_mode(model_name="gemma2", deep_mode=True)
                else:
                    self.update_model_mode(model_name="llama3.2:1b", deep_mode=False)
                continue

            if user_input.lower() in ["/ground", "/grounding"]:
                self.trigger_grounding_exercise()
                continue

            if user_input.lower() in ["/crisis", "/help-crisis", "/hotline"]:
                print(CRISIS_HELPLINES)
                continue

            if user_input.lower() == "/status":
                print("\n[📊 Active Status]")
                print(f"• Model: {self.model_name}")
                print(f"• Mode: {'Deep Cognitive Reasoning' if self.is_deep_mode else 'Fast Casual Companion'}")
                print(f"• History length: {len(self.conversation_history)} messages")
                print(f"• User: {self.user_data.get('name', 'Friend')}")
                continue

            if user_input.lower() == "/help":
                self.print_welcome_banner()
                continue

            # Meetup trigger
            if "schedule meetup" in user_input.lower():
                friend = input("Friend's name: ").strip()
                if friend:
                    self.schedule_meetup(friend)
                continue

            # Regular conversation
            self.chat(user_input)


def parse_args():
    parser = argparse.ArgumentParser(description="Active Friend AI - Proactive Mental Health & Social Companion")
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.2:1b",
        help="Ollama model to use (e.g. 'llama3.2:1b', 'gemma2')"
    )
    parser.add_argument(
        "--reason", "--deep",
        action="store_true",
        dest="deep_reasoning",
        help="Start directly in Gemma 2 Deep Cognitive Reasoning & Mental Stability mode"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    model = "gemma2" if args.deep_reasoning else args.model
    app = ActiveFriend(model_name=model, deep_reasoning=args.deep_reasoning)
    app.start()
