#!/usr/bin/python3
"""
Script to downloaded webpages, extract text and merge all of them
together to create one ebook.
"""

import errno
import os
import re
import epub
from bs4 import BeautifulSoup
from newspaper import Article

name = ""
mainUrl = ""
ch_start = 0
ch_end = 0
nameacr = ""
cover_inp = 1
#Defines a List with no conent
list = []

re_paragraph = re.compile(r"(.+?\n\n|.+?$)", re.MULTILINE)

chapters = []

intro_txt = open("template/intro.txt").read()
credits_txt = open("template/credits.txt").read()


def download(number):
  """Download webpage, extract main article, save result"""
  try:
    url = "%s%d" % (mainUrl, number)
    article = Article(url)
    article.download()
    article.parse()
  except BaseException:
    url = "%s%d-1" % (mainUrl, number)
    article = Article(url)
    article.download()
    article.parse()

  chapterText = ""
  header = False

  for match in re_paragraph.finditer(article.text):
    paragraph = match.group()
    paragraph = paragraph.strip()

    if paragraph != "Previous ChapterNext Chapter":
      if not header:
        chapterText += "<h2>%s</h2>" % (paragraph)

        #Global is used to modify the earlier defined array
        global list
        #inser is used instead of append making it easier to access the vaues
        list.append(paragraph)

        header = True
      else:
        chapterText += "<p>%s</p>\n" % (paragraph)

  chapterHtml = BeautifulSoup(
    """<html>
    <head>
        <title>...</title>
        <link rel="stylesheet" type="text/css" href="style/main.css" />
    </head>
    <body></body>
    </html>""",
    'lxml'
  )
  chapterHtml.head.title.string = article.title
  chapterHtml.body.append(chapterText)

  return str(chapterText)


def packageEbook():
  ebook = epub.EpubBook()
  ebook.set_identifier("ebook-%s" % name)
  ebook.set_title(name)
  ebook.set_language('en')
  doc_style = epub.EpubItem(
    uid="doc_style",
    file_name="style/main.css",
    media_type="text/css",
    content=open("template/style.css").read()
  )
  ebook.add_item(doc_style)
  if cover_inp == 1:
    ebook.set_cover("cover.jpeg", open('Cover/cover.jpeg', 'rb').read())
  
  intro_ch = epub.EpubHtml(title="Introduction", file_name='intro.xhtml')
  intro_ch.add_item(doc_style)
  intro_ch.content = """
  <html>
  <head>
      <title>Introduction</title>
      <link rel="stylesheet" href="style/main.css" type="text/css" />
  </head>
  <body>
      <h1>%s</h1>
      %s
  </body>
  </html>
  """ % (name, intro_txt)
  ebook.add_item(intro_ch)

  credits = epub.EpubHtml(title="Credits", file_name='credits.xhtml')
  credits.add_item(doc_style)
  credits.content = """
  <html>
  <head>
      <title>Credits</title>
      <link rel="stylesheet" href="style/main.css" type="text/css" />
  </head>
  <body>
      <h1>Credits</h1>
      <p> Book Created using wuxiaDownloader</p>
      %s
  </body>
  </html>
  """ % (credits_txt)
  ebook.add_item(credits)

  ebookChapters = []

  i = ch_start
  j = 1
  for chapter_data in chapters:
    chapter = epub.EpubHtml(
      title= list[j-1],
      file_name='%s-Chapter-%d.xhtml' % (nameacr, i)
    )
    chapter.add_item(doc_style)
    chapter.content = chapter_data
    ebook.add_item(chapter)
    ebookChapters.append(chapter)
    j += 1
    i += 1

  # Set the TOC
  ebook.toc = (
    epub.Link('intro.xhtml', 'Introduction', 'intro'),
    (epub.Section('Chapters'), ebookChapters), epub.Link('credits.xhtml', 'Credits', 'credits'),
  )
  # add navigation files
  ebook.add_item(epub.EpubNcx())
  ebook.add_item(epub.EpubNav())
  # Create spine
  nav_page = epub.EpubNav(uid='book_toc', file_name='toc.xhtml')
  nav_page.add_item(doc_style)
  ebook.add_item(nav_page)
  ebook.spine = [intro_ch, nav_page] + ebookChapters + [credits]
  if cover_inp == 1:
    ebook.spine.insert(0, 'cover')
    ebook.guide.insert(0, {
        "type"  : "cover",
        "href"  : "cover.xhtml",
        "title" : "Cover",
    })

  filename = '%s.epub' % (name)
  print("Saving to '%s'" % filename)
  if os.path.exists(filename):
      os.remove(filename)
  epub.write_epub(filename, ebook, {})

def main():
  """User Input + Downloader + Paackager"""
  global name
  global nameacr
  global mainUrl
  global ch_start
  global ch_end
  global cover_inp
  print("Welcome To webnovelDownloader")
  name = input("\nEnter The Full Name of the Book: ")
  nameacr = input("Enter The Acronym Name of the Book: ")
  mainUrl = input("Enter the base Url of the Website.\n(Eg. https://example.org/chapter-): ")
  print("\nChapter Range to download?")
  ch_start = int(input("First chapter: "))
  ch_end = int(input("Last Chapter: "))
  cover_inp = int(input("\nCover \n(If you have placed cover.jpeg in the Image directroy Enter 1 else enter 0): "))
  # Download all chapters one by one
  print("Downloading",(ch_end - ch_start) + 1,"Chapters of", name)
  for i in range(ch_start, ch_end + 1):
    print("Downloading: Chapter", i)
    chapters.append(download(i))

  packageEbook()

  print("Done")


# if yused standalone start the script
if __name__ == '__main__':
  main()

