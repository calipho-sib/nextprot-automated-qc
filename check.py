import os, datetime, re, csv, urllib2, glob, sys, argparse, time
from termcolor import cprint

baseUrl = "https://www.nextprot.org"
lastUrlRequested = ""
lastTextContent = ""
lastHTMLContent = ""

class URLTestResult:
    def __init__(self, URLTest, result):
        self.urlTest = URLTest
        self.result = result

class URLTest:
    def __init__(self, url, expression, value, note):
        self.url = url
        self.expression = expression
        self.value = value
        self.note = note

def cleanHTML(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html.replace("&nbsp;", " "))
  return ' '.join(cleantext.split())

def buildUrl(relativeUrl):
    #If if comes from failures it is already with http
    global baseUrl
    tokens = relativeUrl.split("/")
    if((len(tokens) > 3) and (tokens[3] == "peptides" or tokens[3] == "phenotypes")):
        cprint (relativeUrl + " has an embedded iframe, little hack to get the page... Test can pass to assure quality checks, but the main page URL won't be well indexed by Google.", "yellow") 
        #This is an iframe therefore the url will be different
        iframeUrl = "http://nextp-vm2b.vital-it.ch:8088/render/"+ baseUrl +"/viewers/" + tokens[3] + "/app/index.html%3Fnxentry="+ tokens[2]
        if("alpha" in baseUrl):
            iframeUrl += "&env=alpha" 
        return iframeUrl

    if("?" in relativeUrl):
        return baseUrl + relativeUrl + "&_escaped_fragment_="
    else:
        return baseUrl + relativeUrl + "?_escaped_fragment_="

def getContent(urlTest, params):
    global lastUrlRequested, lastTextContent, lastHTMLContent
    url = buildUrl(urlTest.url)

    #If the url requested is the same, just return the last content
    if(lastUrlRequested != url):
        print("\tHTTP(S)_REQUEST: ... requesting content of " + url + " ...")
        success = True
        maxAttemps = 10
        for x in range(1, (maxAttemps + 1)):
            try: 
                lastHTMLContent = urllib2.urlopen(url).read()
                break
            except Exception, e:
                if(x == maxAttemps):
                    print("FATAL! Failed too many times to request HTTP service, exiting with failure")
                    sys.stdout.flush()
                    sys.exit(1)
                print(e)
                sleeptime = x * 1
                print("Retrying in " + str(sleeptime) + " seconds ... Attempt " + str(x+1) + ", Max attempts: " + str(maxAttemps))
                time.sleep(sleeptime)
                print("\tHTTP(S)_REQUEST: ... requesting content of " + url + " ...")
                sys.stdout.flush()
        lastTextContent = cleanHTML(lastHTMLContent)
        lastUrlRequested = url
    else:
        print("\tCACHED: Taking content of " + url + " from cache")

def checkForEachUrl(urlTest, params):
    getContent(urlTest, params)
    if(urlTest.expression == "containsText" or urlTest.expression == "containsHTML"):
        if(urlTest.expression == "containsText"):
            return urlTest.value in lastTextContent
        else:
            return urlTest.value in lastHTMLContent
    
    elif(urlTest.expression == "!containsText" or urlTest.expression == "!containsHTML"):
        if(urlTest.expression == "!containsText"):
            return urlTest.value not in lastTextContent
        else:
            return urlTest.value not in lastHTMLContent

    elif(urlTest.expression == "countOnceInText"):
        return lastTextContent.count(urlTest.value) == 1

    elif((urlTest.expression == "containsRegexInText") or (urlTest.expression == "containsRegexInHTML")):
        pattern = re.compile(urlTest.value)
        if(urlTest.expression == "containsRegexInText"):
            searchResult = pattern.search(lastTextContent)
        else:
            searchResult = pattern.search(lastHTMLContent)
        if(searchResult is None):
            return False
        return len(searchResult.groups()) > 0

    else:
        print (urlTest.expression + " not known")

def readFile(file):
    urls = []
    cprint ("\nReading tests from " + str(file) + "\n", "blue")
    with open(file) as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        lineCount = 1
        next(reader, None)  # skip the headers
        for row in reader:
            lineCount = lineCount + 1
            if((len(row) > 0) and (not row[0].startswith("#"))):
                try:
                    urls.append(URLTest(row[0], row[1], str(row[2]), row[3]))
                except:
                    print("Failed to read line " + str(lineCount) + " for " + str(file) + " found " + str(len(row)) + " columns. Minimum is 3. Row is: " + str(row))
                    raise
            elif (row[0].startswith("#")):
                cprint("Skipping test: " + str(row), 'yellow')
    return urls

def saveErrors(errors):
    print("Writing remaining errors in errors.tsv")
    f = open("errors.tsv","w+")
    f.write("relativeUrl\texpression\tvalue\tcomment\n")
    for error in errors:
        f.write(error.urlTest.url + "\t" + error.urlTest.expression + "\t" + error.urlTest.value + "\t" + error.urlTest.note + "\n")
    f.close() 

def testFile(file, params):
    urlTestResults = []
    urlTests = readFile(file)
    
    if(params.row):
        urlTests = [urlTests[int(params.row)]]
    else: urlTests = sorted(urlTests, key=lambda ut: ut.url)

    count = 1
    for urlTest in urlTests:
        start = datetime.datetime.now()
        print(str(count) + "/" + str(len(urlTests)) + " Testing\n" + urlTest.url + "\t" +  urlTest.expression + "\t" + urlTest.value + "\t" + urlTest.note + "")
        sys.stdout.flush()
        result = checkForEachUrl(urlTest, params)
        end = datetime.datetime.now()
        diff = end - start
        elapsed_ms = (diff.days * 86400000) + (diff.seconds * 1000) + (diff.microseconds / 1000)
        if(result):
            cprint("\t%s in %d ms" %("Test passed in ", elapsed_ms), 'green')
        else:
            cprint("\t%s in %d ms" %("Failed in", elapsed_ms), 'red')
        urlTestResults.append(URLTestResult(urlTest, result))
        count = count + 1
    return urlTestResults

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Automated neXtprot QC')
    parser.add_argument('--baseUrl', help='the api url example: http://alpha-api.nextprot.org')
    parser.add_argument('--file', help='the file to test (by default takes all files in test-specs)')
    parser.add_argument('--row', help='the row number from the --file to test')

    args = parser.parse_args()

    print("\n########### neXtProt Automated QC configuration ###########################################") 
    if(args.baseUrl):
        baseUrl = args.baseUrl
        print("## --baseUrl: Overriding base url with: " + baseUrl) 
    else:
        print("## --baseUrl: Default base url is: " + baseUrl + ", can be overriden by passing a parameter: python check.py --baseUrl http://alpha-search.nextprot.org")

    report = []
    if(args.file):
        print("## --file: Using file " + args.file) 
        print("###########################################################################################\n") 
        report.extend(testFile(args.file, args))
    else:
        print("## --file: Using all files in folder test-specs") 
        print("###########################################################################################\n") 
        for file in glob.glob("test-specs/*.tsv"):
            report.extend(testFile(file, args))

    errors = filter(lambda x: x.result == False, report)
    if(len(errors) > 0):
        print (str(len(errors)) + "/" + str(len(report)) + " tests failed in " + str(args.file))
        for error in errors:
            print ("\tERROR: " + buildUrl(error.urlTest.url) + " " + error.urlTest.expression + " " + error.urlTest.value)
        saveErrors(errors)
    else:
        if os.path.exists("errors.tsv"):
            os.remove("errors.tsv")
            print("Removing errors file")
        print (str(len(report)) + " tests passed in " + str(args.file))