import urllib
import sys
import getopt
import csv
import os
import http.client
from selenium import webdriver
import urllib.request as ur
import pandas as pd
from bs4 import BeautifulSoup




def check_artists(artist, artists):
    return True
    # if (len(artists) == 0):
    #     return True
    # else:
    #         return artist in artists

def check_types(piece_type, types):
        if (len(types) == 0):
                return True
        else:
                return piece_type in types

def check_object_num(object_num, num_list):
        return object_num in num_list

#returns list of csv lines that the artist matches
def match_lines(met_csv, artists, types, list_file):
        lines = []

        #print(artists)
        if (list_file != ""):
                f = open(list_file, 'r')
                obj_num_list = []
                for line in f:
                        obj_num_list.append(line.strip())
                        
                for row in met_csv:
                        if (check_object_num(row[0], obj_num_list)):
                                lines.append(row)
        else:
                for row in met_csv:
                        if (check_artists(row[18], artists) and check_types(row[31], types)) and bool(row[3]):
                                lines.append(row)

        return lines
        

def download_lines(lines, out_dir, met_csv, ids_already_downloaded, n):
    image_names = []
    curr_n_downloaded = 0
    idx = -1
    success_idxs = []
    descript_texts = []
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(os.path.join(out_dir, "piece_info.csv"), 'wb') as csv_file:
        im_writer = csv.writer(csv_file, delimiter=',')

        for row in met_csv:
            im_writer.writerow(row + ['Image Location'])
            break

        # Note: you will need geckodriver.
        # See https://pypi.org/project/selenium.
        driver = webdriver.Firefox()
        for line in lines:
          idx += 1
          if curr_n_downloaded < n:
              if int(line[4]) not in ids_already_downloaded:
                  print("Starting", line[4], ids_already_downloaded)
                  res = ""
                  try:
                      driver.get('http://www.metmuseum.org/art/collection/search/' + line[4].strip())
                      html = driver.page_source
                  except urllib.URLError:
                      image_names.append(None)
                      print("URL Error")
                      continue

                  offset = html.find("artwork__interaction artwork__interaction--download")

                  soup = BeautifulSoup(html, 'html.parser')
                  descript = soup.find("div", class_="artwork__intro__desc")
                  descript_text =  descript.find('p').getText()

                  if (offset == -1):
                      image_names.append(None)
                      continue
                  offset = html[offset:].find('http') + offset
                  end = html[offset:].find('.jpg') + offset + 4

                  if (end - offset > 300):
                      image_names.append(None)
                      print("URL Error")
                      continue

                  image_link = html[offset:end]
                  print("link\n", image_link)

                  image_name = image_link.split('/')[-1]
                  
                  image_path = os.path.join(out_dir, image_name)
                  
                  image_file = ""
            
                  success = False
                  try:
                      image_file = ur.urlopen(image_link)
                      success_idxs.append(idx)
                      image_names.append(image_name)
                      descript_texts.append(descript_text)
                      curr_n_downloaded += 1
                  except :
                      #image_names.append(None)
                      print("URL error, skipping")
                      continue                

                  with open(image_path, 'wb') as output:
                      output.write(image_file.read())


              else:
                  print("Skipping", line[4], " already obtained")
                  
        return  success_idxs, image_names, descript_texts
                

def main(argv):
        opts, args = getopt.getopt(argv, "i:o:a:t:l:", ["csv=", "out=", "artist=", "type=", "list=", "logfile=", "num="])

        met_csv_file = ""
        out_dir = ""
        list_file = ""
        logfile = ""
        N = 0
        artists = []

        types = []

        for opt, arg in opts:
                if opt in ("--csv", "-i"):
                        met_csv_file = arg
                elif opt in ("--out", "-o"):
                        out_dir = arg
                elif opt in ("--artist", "-a"):
                        artists = arg.split(':')
                elif opt in ("--type", "-t"):
                        types = arg.split(":")
                elif opt in ("--list", "-l"):
                        list_file = arg
                elif opt in ("--logfile", "-lg"):
                        logfile = arg
                elif opt in ("--num", "-n"):
                        n = int(arg)

        met_csv = csv.reader(open(met_csv_file, 'r'), delimiter=',')

        csv_lines = match_lines(met_csv, artists, types, list_file)

        #lines = 0
        #for line in csv_lines:
                #print(line[18] + " " + line[31] + " " + line[9] + " " + line[4] + "\ntags:" + line[51])
                #lines += 1

        #print(lines)

        existing_df = pd.read_csv(logfile, sep="\t")
        ids_already_downloaded = existing_df['MET_Object_ID'].tolist()

        #print(ids_already_downloaded)
        #print("\n\n\n")
        
        successes, img_names, descripts = download_lines(csv_lines, out_dir, met_csv, ids_already_downloaded, n)

        with open(logfile, 'a') as log:
            for i, succ in enumerate(successes):
                print(i, "Success ", succ)
                line = csv_lines[succ]

                # Filename, Title, Artist, Medium, Tags, MET_Object_ID,
                try:
                    print(img_names[i] + "\t" + line[9] + "\t" + line[18] + "\t" + line[31] + "\t" + line[51] + "\t" + line[4] + "\n")
                    csvrow = img_names[i] + "\t" + line[9] + "\t" + line[18] + "\t" + line[31] + "\t" + line[51] + "\t" + line[4] + "\t" + descripts[i] + "\n"
                    log.write(csvrow)
                except:
                    print("exception", i, csv_lines[i-1], csv_lines[i], csv_lines[i+1])
                    pass
                    
            


if __name__ == "__main__":
        main(sys.argv[1:])

        
