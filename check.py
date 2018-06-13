import re, csv, urllib2, glob, sys, argparse
import datetime
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
    #If if comes from failures it is already with http
    global baseUrl
    return baseUrl + relativeUrl + "?_escaped_fragment_="

def checkForEachUrl(urlTest, params):
    global lastUrlRequested, lastContent
    if(params.baseUrl):
	url = buildUrl(urlTest.url)
    else:
        url = buildUrl(urlTest.url)

    #If the url requested is the same, just return the last content
    if(lastUrlRequested != url):
        print("\tHTTP(S)_REQUEST: ... requesting content of " + url + " ...")
        content = urllib2.urlopen(url).read()
        lastUrlRequested = url
        lastContent = content
    else:
        print("\tCACHED: Taking content of " + url + " from cache")
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
                    if((not row[1] == "containsRegex") and (("ANY500CHARS" in str(row[2])) or ("ANY100CHARS" in str(row[2])) or ("ANY20CHARS" in str(row[2])))):
                        cprint("Using keyword ...ANY[20|100|500]CHARS... and expression is different than containsRegex in line " + str(lineCount) + " using " + str(row[1] != "containsRegex"), 'yellow')
                    urls.append(URLTest(row[0], row[1], str(row[2]).replace("...ANY20CHARS...", "((.|\\n|\\r){1,20})").replace("...ANY100CHARS...", "((.|\\n|\\r){1,100})").replace("...ANY500CHARS...", "((.|\\n|\\r){1,500})"), row[3]))
                except:
                    print("Failed to read line " + str(lineCount) + " for " + str(file) + " found " + str(len(row)) + " columns. Minimum is 3. Row is: " + str(row));
                    raise;
                    sys.exit(1);
    return urls;

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
    urlTests = sorted(urlTests, key=lambda ut: ut.url)
    count = 1
    for urlTest in urlTests:
        start = datetime.datetime.now()
        print(str(count) + "/" + str(len(urlTests)) + " Testing " + urlTest.url + "\t" +  urlTest.expression + "\t" + urlTest.value + "\n\tSpec: " + urlTest.note + "")
        result = checkForEachUrl(urlTest, params)
        end = datetime.datetime.now()
        diff = end - start
        elapsed_ms = (diff.days * 86400000) + (diff.seconds * 1000) + (diff.microseconds / 1000)
        if(result):
            cprint("\t%s in %d ms" %("OK", elapsed_ms), 'green')
        else:
            cprint("\t%s in %d ms" %("ERROR", elapsed_ms), 'red')
        count = count + 1
        urlTestResults.append(URLTestResult(urlTest, result))
    errors = filter(lambda x: x.result == False, urlTestResults)
    if(len(errors) > 0):
        global success
        success = False
        print (str(len(errors)) + "/" + str(len(urlTestResults)) + " tests failed in " + file)
        for error in errors:
            print ("\tERROR: " + buildUrl(error.urlTest.url) + " " + error.urlTest.expression + " " + error.urlTest.value)
        saveErrors(errors)
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

    print("\n########### neXtProt Automated QC configuration ###########################################") 
    if(args.baseUrl):
        baseUrl = args.baseUrl;
        print("## --baseUrl: Overriding base url with: " + baseUrl) 
    else:
        print("## --baseUrl: Default base url is: " + baseUrl + ", can be overriden by passing a parameter: python check.py --baseUrl http://alpha-search.nextprot.org")

    if(args.file):
        print("## --file: Using file " + args.file) 
        print("###########################################################################################\n") 
        testFile(args.file, args)
    else:
        print("## --file: Using all files in folder test-specs") 
        print("###########################################################################################\n") 
        for file in glob.glob("test-specs/*.tsv"):
            testFile(file, args)
