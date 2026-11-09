# InterviewMate test checklist

## Automated checks completed for this package
- Python syntax compilation: `app.py` and `interview_bot.py`.
- Offline answer-classification smoke tests: complete technical answer, partial answer, explicit “I don't know”, short answer, and irrelevant answer.
- ZIP integrity check.

## Manual browser tests still required
- Start Streamlit in current Chrome/Edge and grant camera/microphone permission.
- Verify speech synthesis is audible and recognition captures a complete answer.
- Confirm speech playback ends before the microphone listening phase starts.
- Confirm the 5-second post-speech silence submits only once.
- Confirm manual end and camera warning 10 stop speech and microphone immediately.
- Test responsive desktop/mobile layout and all existing profile, resume, matching, dashboard, and history pages.
- With `ANTHROPIC_API_KEY` configured, test real model interpretation, network failure, rate limits, and malformed model output.

## Known limitations
- Offline classification is heuristic, not semantic AI. It uses expected concepts, answer length, and basic relevance cues; it can misclassify nuanced answers.
- The Claude integration requires a valid Anthropic API key, internet access, and a model name available to that key.
- Live camera/microphone behavior cannot be fully verified without a browser session and physical devices.
