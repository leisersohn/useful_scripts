import sys
import xlrd
import csv

xlsx_filename = sys.argv[1]
xlsx_sheetname = sys.argv[2]

if xlsx_filename and xlsx_sheetname:
    wb = xlrd.open_workbook(xlsx_filename)
    sh = wb.sheet_by_name(xlsx_sheetname)
    csv_filename = xlsx_filename.replace('.xlsx','.csv')
    csv_output = open(csv_filename,'w')

    wr = csv.writer(csv_output, dialect='excel')

    for rownum in range(sh.nrows):
        wr.writerow(sh.row_values(rownum))

    csv_output.close()

