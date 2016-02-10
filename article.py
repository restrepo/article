#!/usr/bin/env python
'''
Module article: Fill article object from DOI
json: from DOI API
citations: from Google Scholar
Colciencias Info from ISSN or Journal name: depends on json
'''
import time
import requests
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth',500)

def keysdash2underscore(ds):
    '''
    Convert keys with dash  to keys with underscore
    '''
    dfk=pd.DataFrame(ds.keys(),columns=['keys'])
    for k in dfk[dfk['keys'].str.contains('[A-Za-z]+-[A-Za-z]')].values:
        ds[k[0].replace('-','_')]=ds[k[0]]
        
    return ds

class article(object):
    '''
    Obtain info from D0I
    '''
    urldoi='http://dx.doi.org/'
    citedby=pd.Series()
    json=pd.Series()
    def __init__(self,doi='10.1007/JHEP11(2013)011',citations=True,json=True,colciencias=True):
        self.doi=doi.replace(self.urldoi,'')
        #print 'TODO: JSON metadata here'
        
        if citations:
            r=requests.get('https://scholar.google.com/scholar?q=%s' %self.urldoi+self.doi)
            time.sleep(2)
            sep='">Cited by'
            self.citedby['number']='';self.citedby['url']=''
            if r.text.find(sep)!=-1:
                rr=r.text.split(sep)
                self.citedby['number']=rr[1].split('</a>')[0].strip()
                self.citedby['url']='https://scholar.google.com%s' %rr[0].split('<a href="')[-1]
                
        if json:    
            r=requests.get(self.urldoi+self.doi,\
                       headers ={'Accept': 'application/citeproc+json'})
            if r.status_code==200:
                self.json=pd.Series(r.json())
                self.json=keysdash2underscore(self.json)
                for k in self.json.keys():
                    if type(self.json[k])==dict:
                        self.json[k]=pd.Series(self.json[k])
                        self.json[k]=keysdash2underscore(self.json[k])
                        
                    if type(self.json[k])==list:
                        if k=='author' or k=='funder' or k=='license' or k=='link':
                            if self.json[k]:
                                self.json[k]=pd.DataFrame(self.json[k])
                        if k=='subject' or k=='subtitle':
                            if self.json[k]:
                                self.json[k]=self.json[k][0]
                #proper sub-Series for nested json keys...

if __name__ == "__main__":                
    a=article(doi='http://dx.doi.org/10.1103/PhysRevD.92.013005')
    print a.citedby.number
    print a.json.author.to_string