import sys
import os

proj_root = os.path.dirname(os.path.dirname(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from agents import generate_report


def main():
    try:
        content = generate_report(
            "Python programming",
            "Title: Python\nURL: https://python.org\nSnippet: Python is a popular programming language.",
        )
        print("Report:\n", content[:500])
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
