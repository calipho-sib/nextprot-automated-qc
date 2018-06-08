import re, csv, urllib2, glob, sys, argparse
from termcolor import cprint

success = True
baseUrl = "https://www.nextprot.org"
lastUrlRequested = ""
lastContent = ""

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

def buildUrl(relativeUrl):
    global baseUrl
    return baseUrl + relativeUrl + "?_escaped_fragment_="

def checkForEachUrl(urlTest, params):
    global lastUrlRequested, lastContent
    if(params.baseUrl):
	url = buildUrl(urlTest.url)
    else:
        url = buildUrl(urlTest.url)
    #print("Requesting " + url + " ...")
    #If the url requested is the same, just return the last content
    if(lastUrlRequested != url):
        content = urllib2.urlopen(url).read()
        lastUrlRequested = url
        lastContent = content
    else:
        content = lastContent

    if(urlTest.expression == "containsText"):
        return urlTest.value in content
    if(urlTest.expression == "containsRegex"):
        pattern = re.compile(urlTest.value)
        searchResult = pattern.search(content)
        if(searchResult is None):
            return False
        return len(searchResult.groups()) > 0
    if(urlTest.expression == "!containsText"):
        return urlTest.value not in content
    print (urlTest.expression + " not known");

def readFile(file):
    urls = []
    print ("Reading " + str(file))
    with open(file) as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        lineCount = 1
        next(reader, None)  # skip the headers
        for row in reader:
            lineCount = lineCount + 1
            if((len(row) > 0) and (not row[0].startswith("#"))):
                try:
                    urls.append(URLTest(row[0], row[1], row[2], row[3]))
                except:
                    print("Failed to read line " + str(lineCount) + " for " + str(file) + " found " + str(len(row)) + " columns. Minimum is 3. Row is: " + str(row));
                    sys.exit(1);
                    raise;
    return urls;

def testFile(file, params):
    urlTestResults = []
    urlTests = readFile(file)
    for urlTest in urlTests:
        print("Testing " + urlTest.url + "\t" +  urlTest.expression + "\t" + urlTest.value + "\n\t" + urlTest.note + "")
        result = checkForEachUrl(urlTest, params)
        if(result):
            cprint("\tOK", 'green')
        else:
            cprint("\tERROR", 'red')
        urlTestResults.append(URLTestResult(urlTest, result))
    errors = filter(lambda x: x.result == False, urlTestResults)
    if(len(errors) > 0):
        global success
        success = False
        print (str(len(errors)) + "/" + str(len(urlTestResults)) + " tests failed in " + file)
        for error in errors:
            print ("\tERROR: " + buildUrl(error.urlTest.url) + " " + error.urlTest.expression + " " + error.urlTest.value)
    else:
        print (str(len(urlTestResults)) + " tests passed in " + file)


if(not success):
    print "JOB FAILED!"
    sys.exit(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Automated neXtprot QC')
    parser.add_argument('--baseUrl', help='the api url example: http://alpha-api.nextprot.org')
    parser.add_argument('--file', help='the file to test (by default takes all files in test-specs)')

    args = parser.parse_args()

    if(args.baseUrl):
        baseUrl = args.baseUrl;
        print("Overriding base url to " + baseUrl) 
    else:
        print("Default base url is: " + baseUrl + ", can be overriden by passing a parameter: python check.py --baseUrl http://alpha-search.nextprot.org")

    if(args.file):
        testFile(args.file, args)
    else:
        print ("Checking for all files in test-specs folder")
        for file in glob.glob("test-specs/*.tsv"):
            testFile(file, args)
