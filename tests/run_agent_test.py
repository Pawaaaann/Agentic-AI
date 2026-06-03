import sys
import os
# ensure project root is on sys.path so `agents` can be imported when running from anywhere
proj_root = os.path.dirname(os.path.dirname(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from agents import llm

def main():
    try:
        messages = [
            ("system", "You are a concise test assistant."),
            ("human", "Write a one-sentence summary about the Python programming language.")
        ]
        ai_msg = llm.invoke(messages)
        # ai_msg may be an object with .content or a plain string
        content = getattr(ai_msg, 'content', ai_msg)
        print("AI response:\n", content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    main()
