from pprint import pprint
import csv
def get_hrefs(file_name = 'all_hrefs.txt', csv_name = 'all_hrefs.csv'):
    hrefs = []
    with open('./hrefs/' + file_name, 'rb') as data:
        res = data.readline()
        while res:
            res = res.decode()
            if '/spell' in res:
                hrefs.append(res[13:res.find('">')])
            res = data.readline()
    with open('./hrefs/' + csv_name, 'w') as fp:
        writer = csv.writer(fp)
        writer.writerow(hrefs)
        
get_hrefs('rogue.txt', 'rogue.csv')
get_hrefs('fighter.txt', 'fighter.csv')
get_hrefs()