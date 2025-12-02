import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from typing import List, Optional
import re
import json

app = FastAPI(
    title= "Truyen Tranh Scraper API",
    description="API nay cao URL anh tu trang web truyen tranh cu the"
)

#Header giúp giả lập trình duyệt để tránh bị chặn
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

root_url = "https://aquastarsleep.co.uk"
reflex_url = "http://10.0.2.2:8000/api/v1/manga"
class Story:
    def __init__(self, name = None, img_cover = None, story_link = None, chapter = None, chapter_link = None, chapter_release = None, number_view = None, star_rating = None):
        self.name = name
        self.img_cover = img_cover
        self.story_link = story_link
        self.chapter = chapter
        self.chapter_link = chapter_link
        self.chapter_release = chapter_release
        self.number_view = number_view
        self.star_rating = star_rating
        self.kind_story = None
        self.manufacturer = None
        self.dest = None
        self.chapters = []

    def __str__(self):
        return f"{self.name}||{self.chapter}|| {self.chapter_release}||{self.img_cover}||{self.story_link}||{self.number_view}||{self.star_rating}"

def crawl_story_names(page_number: int) -> Optional[list[Story]]:
    # "https://aquastarsleep.co.uk/tim-kiem?r=newly-updated&page=1
    url = f"{root_url}/tim-kiem?r=newly-updated&page={page_number}"
    
    try:
        response = requests.get(url = url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, 'html.parser')

        storys = {}

        #Get Story name, link, image_cover
        elements = soup.find_all('div', class_ = 'p-thumb flex-shrink-0')
        
        if not elements:
            return []
        for e in elements:
            link = f"{e.a.get('href')}"
            name = e.a.get('title')
            img_cover = e.a.span.img.get('data-src')
            storys[name] = Story(name, img_cover, link)

        #Get Story_name, number_view, 
        elements = soup.find_all('div', class_ = 'p-content flex-grow-1')

        if not elements:
            return []

        for e in elements:
            name = e.h3.a.string
            storys[name].chapter_link = f"{e.ul.li.a.get('href')}"
            storys[name].chapter = e.ul.li.a.get('href').split("/")[-1].capitalize()
            storys[name].chapter_release = e.ul.li.a.span.string
            storys[name].number_view = e.find('span', class_="num-view").string
            storys[name].star_rating = e.div.find_all('span')[2].string
    
        # for s in storys.values():
        #     print(s)
        return storys.values()
    except requests.exceptions.RequestException as e:
        print(f"There is an error when access {e}")


# crawl_story_names(1)

@app.get("/api/v1/manga/{page_number}")
async def get_story_name(page_number: int):
    if page_number <= 0:
        raise HTTPException(status_code=400, detail="Page number must > 0")
    
    storys = crawl_story_names(page_number)

    if storys is None:
        raise HTTPException(status_code=404, detail=f"Not found story{page_number}")

    if not storys:
        raise HTTPException(status_code=404, detail=f"Found a web but there is no story in page{page_number}, the structure of HTML can be change")
    
    objs = []

    for story in storys:
        objs.append({
            "story name": story.name,
            "chapter name": story.chapter,
            "chapter link": story.chapter_link,
            "chapter release": story.chapter_release,
            "story link": story.story_link,
            "link image": story.img_cover,
            "number view": story.number_view,
            "star rating": float(story.star_rating)

        })
    return objs

class Chapter:
    def __init__(self, chapter_name, link_chapter, time, number_view):
        self.chapter_name = chapter_name
        self.link_chapter = link_chapter
        self.time = time
        self.number_view = number_view
    def __str__(self):
        return f"{self.chapter_name}||{self.link_chapter}||{self.time}||{self.number_view}"



def crawl_list_chapters(story_name: str) -> Optional[Story]:
    url = f"{root_url}/truyen-tranh/{story_name}"
    try:
        response = requests.get(url, headers = headers, timeout=15)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        story = Story()
        story.kind_story = soup.find('div', class_="kind").img.string
        story.manufacturer = soup.find('div', class_="kind").img.get("src").split("/")[-1].split(".")[0].upper()
        story.dest = soup.find('div', class_="line-clamp html-content").get_text(separator="\n", strip=True)
        
        elements = soup.find_all('div', class_ = "l-chapter") 

        if not elements:
            return []
        
        list_chapters = []
        
        for e in elements:        
            chapter_name = e.a.get('title')
            link_chapter = f"{e.a.get('href')}"
            time = e.find_all('span')[0].string.strip()
            number_view = e.find_all('span')[1].string.strip()
            list_chapters.append(Chapter(chapter_name, link_chapter, time, number_view))
        story.chapters = list_chapters
        print(story)

        return story
    except requests.exceptions.RequestException as e:
        print(f"There is an error when access {e}")


crawl_list_chapters("vo-luyen-dinh-phong")
@app.get("/api/v1/manga/truyen-tranh/{story_name}")
async def get_chapter_list(story_name: str):
    if not story_name or story_name == "":
        raise HTTPException(status_code=404, detail="There is empty story name")
    story = crawl_list_chapters(story_name)

    if story is None:
        raise HTTPException(status_code=404, detail=f"Not found story{story_name}")
    if not story:
        raise HTTPException(status_code=404, detail="Found web but there is no chapters") 
    
    
    
    json_chapters = []
    for ch in story.chapters:
        json_chapters.append(
            {
                "chapterName": ch.chapter_name,
                "link chapter": ch.link_chapter,
                "number view" : ch.number_view,
                "chapterDate": ch.time
            }
        )
    rest = {
        "kind story": story.kind_story,
        "manufacturer": story.manufacturer,
        "description": story.dest,
        "chapters": json_chapters
    }
    return rest


def crawl_chapter_images(story_name: str, chapter_number: str) -> Optional[List[str]]:
    """ Scrape cac URL anh tu một chương truyện cụ thể"""

    #Xây dựng URL mục tiêu
    # base_manga_name = "vo-luyen-dinh-phong"
    url = f"{root_url}/truyen-tranh/{story_name}/{chapter_number}"

    try:
        response = requests.get(url, headers = headers, timeout=15)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all('img', class_ = re.compile('reading-img', re.IGNORECASE)) 
        
        if not elements:
            return []

        img_urls = []
        for e in elements:
            img_url = e.get('src')
            if img_url != None and img_url.startswith("https"):
                img_urls.append(img_url)

            img_url = e.get('data-src')
            if img_url != None and  img_url.startswith("https"):
                img_urls.append(img_url)
        return img_urls
    except requests.exceptions.RequestException as e:
        print(f"There is an error when access {e}")
        
#define Endpoint API
# /api/v1/manga/truyen-tranh/tuyet-the-vo-than/chapter-1076
# @app.get("/api/v1/manga/chapter/{chapter_number}")
@app.get("/api/v1/manga/truyen-tranh/{story_name}/{chapter_number}")
async def get_chapter_data(story_name: str, chapter_number: str):
    """
    API get list url image of chapter
    """
    if not story_name or not chapter_number:
        raise HTTPException(status_code=400, detail="There is an empty story name or chapter number")
    #crawls data
    img_list = crawl_chapter_images(story_name, chapter_number)
    # print(img_list)

    if img_list is None:
        raise HTTPException(status_code=404, detail=f"Not found chapter{chapter_number}")

    if not img_list:
        raise HTTPException(status_code=404, detail=f"Found web but there is no image in chapter{chapter_number}, The stucture of HTML can be change")
    return {
        "chapter": chapter_number, 
        "manga_name": "Võ Luyện Đỉnh Phong",
        "total_images": len(img_list),
        "images": img_list
    }


