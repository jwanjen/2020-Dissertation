#Logging output to remove prints
import logging

#To connect to the webpage
from  requests_html import HTMLSession

#To hold pages to visit
from collections import deque


def getLinks(thePage):
    """
    Search the page for links in the article Body

    @param thePage:  The request from session.get(URL)
    @return:  List of all the links in the content body

    """

    bodyText = thePage.html.find(".story-body__inner")

    bodyLinks = bodyText[0].links
    return bodyLinks


def getTitle(thePage):
    """Get the page title

    @param thePage:  Request from session
    @return Page Headline
    """

    headerElement = thePage.html.find("h1")[0]
    return headerElement.text
    

def parseText(theText, keywordList):
    """Parse a block of text looking for keywords disregarding case sensitivity.  

    @param theText:  The request from session.get(URL)
    @param keywordList:  List of keywords to search for

    @return Dict of {<keyword>: <count>}

    """
    
    tempDict = {}

    #Pull out the relevant part of the body 
    bodyText = theText.html.find(".story-body__inner")[0]

    #Scans and keeps a record of keyword count
    for item in keywordList:
       tempDict[item] = bodyText.text.lower().count(item.lower())
    return tempDict


def getTopics(thePage):
    """
    Scan a page for Topic Based Tags
    
    It appears that news articles have a standard structure.
    The "Related Topics" sections contain links to the most recent articles with a given tag. Relevant Div is <div id="topic-tags"> 
    We can scan for these to continue our crawling.


    @param thePage:  The request from the session.get(URL)
    @return:  A List of all topic tags we have found
    """
    tags = []

    #Search for the Div with id "topic-tags" that is used to hold topics
    topicTags = page.html.find("#topic-tags")

    #As this may return multiple matches, lets iterate through them to turn it into one list
    for item in topicTags:
        tags.extend(item.links)

    #and Return 
    return tags
    

def parseTopicsPage(thePage):
    """
    Parse a topics page for information

    Again topics page has a load of cruft on it
    We can filter that out by restricting procesing to the
    "main-content" id. 

    @param thePage: A page as returned by a topic query
    @return A list of all the links on that page
    """

    #Get the content. 
    mainContent = thePage.html.find("#main-content")[0]


class BBCScraper:
    """
    Scrape the BBC website
    """

    def __init__(self, keywords = []):
        """
        Setup Relevant Global Variables

        @param:  Optional list of keywords
        """

        #Setup log
        self.log = logging.getLogger(__name__)
        self.log.debug("Initialise Scraper")
        
        #HTML Requsts session
        self.session = HTMLSession()

        #Pages we have visited
        self.visitedPages = []

        #Pages in the list to visit
        self.pageList = deque()

        #List of Keywords we are looking for
        self.keywords = keywords

        #And a Count of Keywords (as a Dict)
        self.keywordCount = {}

    def runIterative(self, URL, maxItems=10):
        """
        Scan the pages in an iterative way
        
        Given a starting page 

           - Scan it for keywords and log them.
           - Append any links to the list of pages to visit
           - Scan next page in the list if we have not visited it

        This will stop after visiting *maxItems* pages

        @param URL:  Initial URL to visit
        @param MaxItems: Maximum Number of pages to scan
        """

        #Intialise our counter
        counter = 0
        
        #Initialise the page list
        self.pageList.append(URL)

        #Loop until we are told to stop
        while True:
            if counter >= maxItems:
                self.log.info("Maximum Pages Scanned. Stopping")
                return

            #Stop if we run out out items
            try:
                nextItem = self.pageList.popleft()
            except IndexError:
                self.log.info("Queue has run out of items. Exiting")
                return

            self.log.debug("Scanning URL {0}".format(nextItem))
            #And check if we have visited this URL previously
            if nextItem in self.visitedPages:
                self.log.debug("--> URL Visited. Ignoring")
            else:
                #Scan the Page
                self.scanPage(nextItem)
                self.visitedPages.append(nextItem)
                counter += 1

            
    def scanPage(self, URL):
        """
        Scan a page and update the counts

        @param URL: URL to Scan
        """
        self.log.info("Getting page {0}".format(URL))
        page = self.session.get(URL)

        pageTitle =  getTitle(page)
        self.log.debug("--> Page Title {0}".format(pageTitle))
        
        #Get relevant Links
        try:
            bodyLinks = getLinks(page)
            self.log.debug("--> Page Links: {0}".format(bodyLinks))

            #We need to do some processing here

            for link in bodyLinks:

                if link.startswith("https://bbc.co.uk"):
                    self.pageList.append(link)
                #Fix relitive Links                    
                elif link.startswith("/"):
                    newLink = "https://bbc.co.uk{0}".format(link)
                    self.pageList.append(newLink)
                else:
                    #Otherwise it's not a BBC Link
                    pass
                    
            #self.pageList.extend(bodyLinks)
        except IndexError:
            self.log.info("--> Page has no Links")
        
        #Get a count of Tags
        try:
            tagCount = parseText(page, self.keywords)
            self.log.debug("--> Page Tags: {0}".format(tagCount))

            #OK we also want the page title
            
            #We can update our keywords    
            self.keywordCount[URL] = (pageTitle, tagCount)

        except:
            self.log.info("--> Page has no Text")


#The actual program starts from here        
if __name__ == "__main__":
    #Setup logging
    logging.basicConfig(level = logging.INFO)
    #Hide the URLLib Logs
    logging.getLogger("urllib3").setLevel(logging.INFO)

    #The URL to scrape
    URL = "https://www.bbc.co.uk/news/technology-52319093"
    
    #Keywords to search for on scrape
    keywords = ["ASD", "Anger", "Bipolar Disorder", "Boredom", "Curiosity", "Cyber-terrorist", "Cyberterrorism", "Cyberterrorist", "Depression", "Ego", "Fun", "Justice", "Manipulative", "Narcissism", "Neurotic", "PTSD", "Pride", "Revenge", "Schizophrenia", "Terrorist", "Thrill", "Unspecified Personality Disorder"]
    
    scanner = BBCScraper(keywords)
    scanner.runIterative(URL)

    #Print the output on terminal
    import pprint
    pprint.pprint(scanner.keywordCount)

