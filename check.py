import csv, urllib2, glob, sys

success = True
urlBase = "https://www.nextprot.org"

class URLTestResult:
    def __init__(self, URLTest, result):
        self.urlTest = URLTest
        self.result = result

class URLTest:
    def __init__(self, url, expression, value):
        self.url = url
        self.expression = expression
        self.value = value


def buildUrl(relativeUrl):
    return urlBase + relativeUrl + "?_escaped_fragment_="


def checkForEachUrl(urlTest):
    url = buildUrl(urlTest.url)
    content = urllib2.urlopen(url).read()
    if(urlTest.expression == "containsText"):
        return urlTest.value in content
    if(urlTest.expression == "!containsText"):
        return urlTest.value not in content
    print (urlTest.expression + " not known");

def readFile(file):
    urls = []
    with open(file) as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        next(reader, None)  # skip the headers
        for row in reader:
            if((len(row) > 0) and (not row[0].startswith("#"))):
                urls.append(URLTest(row[0], row[1], row[2]))
    return urls;

def testFile(file):
    urlTestResults = []
    urlTests = readFile(file)
    for urlTest in urlTests:
        result = checkForEachUrl(urlTest)
        urlTestResults.append(URLTestResult(urlTest, result))
    errors = filter(lambda x: x.result == False, urlTestResults)
    if(len(errors) > 0):
        success = False
        print (str(len(errors)) + "/" + str(len(urlTestResults)) + " tests failed in " + file)
        for error in errors:
            print ("\tERROR: " + buildUrl(error.urlTest.url) + " " + error.urlTest.expression + " " + error.urlTest.value)
    else:
        print (str(len(urlTestResults)) + " tests passed in " + file)

for file in glob.glob("test-specs/*.tsv"):
    testFile(file)

if(not success):
    sys.exit(1)