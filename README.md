# omni-scraper

I wrote this tool, based on the C# example for Omnivore's GraphQL API so that I
could download the articles that I save to Omnivore. The original intention is
to simply keep a local copy of them, but I will probably change over time, as I
am wanting to use this to assist in the development of a personal
"weekly roundup" newsletter to share what I have been reading and learning.

This is far from good code, in any meaning of the word. It does what I need it
to and I'll clean it up as I expand this into a proper project.

## Usage Instructions

```sh
$ python3 -m pip3 install -r requirements.txt
$ cp .env.example .env # and adjust values as necessary
$ python3 omni-scraper.py
```
