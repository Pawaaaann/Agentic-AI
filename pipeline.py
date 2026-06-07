from agents import build_reader_agent, build_search_agent, generate_report


def run_research_pipeline(topic: str) -> dict:
    state = {}

    print("\n" + "=" * 50)
    print("step 1 - search agent is working ...")
    print("=" * 50)

    search_agent = build_search_agent()
    state["search_results"] = search_agent(
        f"Find recent, reliable and detailed information about: {topic}"
    )
    print("\n search result ", state["search_results"])

    print("\n" + "=" * 50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("=" * 50)

    reader_agent = build_reader_agent()
    urls = [
        line.split("URL: ")[1].split("\n")[0]
        for line in state["search_results"].split("\n")
        if "URL: " in line
    ]
    if urls:
        state["scraped_content"] = reader_agent(urls[0])
    else:
        state["scraped_content"] = "No URLs found in search results"
    print("\nscraped content: \n", state["scraped_content"])

    print("\n" + "=" * 50)
    print("step 3 - Writer is drafting the report ...")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )
    state["report"] = generate_report(topic, research_combined)

    print("\n Final Report\n", state["report"])
    return state


if __name__ == "__main__":
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)
