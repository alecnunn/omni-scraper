import json
import os
import time
import asyncio
import aiofiles
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("OMNIVORE_API_URL", "https://api-prod.omnivore.app/api/graphql")
SEARCH_TERM = os.getenv("SEARCH_TERM", "")
DOCUMENTS_DIR = "docs"
MAX_REQUESTS_PER_SECOND = int(os.getenv("MAX_REQUESTS_PER_SECOND", "2"))
SEMAPHORE_VALUE = int(os.getenv("SEMAPHORE_VALUE", "5"))
AUTH_TOKEN = os.getenv("OMNIVORE_AUTH_TOKEN")

# Ensure the documents directory exists
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Global variables
semaphore = asyncio.Semaphore(SEMAPHORE_VALUE)
last_request_time = 0

# GraphQL query
SEARCH_QUERY = """
    query Search(
        $after: String
        $first: Int
        $query: String
        $includeContent: Boolean
        $format: String
    ) {
        search(
            after: $after
            first: $first
            query: $query
            includeContent: $includeContent
            format: $format
        ) {
            ... on SearchSuccess {
                edges {
                    node {
                        id
                        title
                        url
                        content
                        slug
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                    totalCount
                }
            }
            ... on SearchError {
                errorCodes
            }
        }
    }
"""

async def fetch_page(session, cursor, limit, search_query):
    global last_request_time
    async with semaphore:
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        if time_since_last_request < 1 / MAX_REQUESTS_PER_SECOND:
            await asyncio.sleep(1 / MAX_REQUESTS_PER_SECOND - time_since_last_request)
        
        variables = {
            "after": cursor,
            "first": limit,
            "format": "markdown",
            "includeContent": True,
            "query": search_query,
        }
        
        async with session.post(
            API_URL,
            json={"query": SEARCH_QUERY, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Cookie": f"auth={AUTH_TOKEN};"
            }
        ) as response:
            response.raise_for_status()
            result = await response.json()
            last_request_time = time.time()
            return result["data"]["search"]

async def fetch_all_links(session, start, search_query):
    cursor = start
    has_next_page = True
    while has_next_page:
        next_page = await fetch_page(session, cursor, 10, search_query)
        if next_page is None:
            break

        if next_page.get("edges"):
            for edge in next_page["edges"]:
                yield edge["node"]
        cursor = next_page["pageInfo"].get("endCursor")
        has_next_page = next_page["pageInfo"].get("hasNextPage", False)

async def save_item(item):
    filename = f"{DOCUMENTS_DIR}/{item['id']}.md"
    content = f"Title: {item['title']}\nURL: {item['url']}\n{'-' * 25}\n\n{item['content']}"
    
    async with aiofiles.open(filename, "w") as file:
        await file.write(content)
    print(f"Saved {item['title']}")

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        async for item in fetch_all_links(session, None, SEARCH_TERM):
            task = asyncio.create_task(save_item(item))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
