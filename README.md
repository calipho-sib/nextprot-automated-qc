#Quality Control automated tests

## Run tests options

Run the test in production www.nextprot.org (ensures SEO rendering tools are working, as well)
```shell
python check.py 
```
Test in alpha environment
```shell
python check.py --baseUrl http://alpha-search.nextprot.org
```

Test in alpha environment with a particular test file
```shell
python check.py --baseUrl http://alpha-search.nextprot.org --file test-specs/terms-view.tsv
```

Test in alpha environment for one row of the file
```shell
python check.py --baseUrl http://alpha-search.nextprot.org --file test-specs/terms-view.tsv --row 2
```

## Tests configuration

All tests are located in [test-specs](/test-specs)

### Expressions

* containsText - Expects to find a certain string in text
* containsHTML - Expects to find some HTML in text (can be used for http links for example)
* !containsText - Does not expect to find a certain string in text 
* !containsHTML -  Does not expect to contain some HTML (can be used for http links for example)
* countOnceInText - Expects to find only once the occurence of a certain text
* containsRegexInText - Tries to match a certain regex against the text version 
* containsRegexInHTML  - Tries to match a certain regex against the HTML version