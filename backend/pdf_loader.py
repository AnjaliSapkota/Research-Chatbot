import pymupdf # import PyMuPDF

doc = pymupdf.open("Inception Report_IIDS_Jan2026.pdf") # open a supported document

page = doc[0] # load the required page (0-based index)

text = page.get_text() # extract plain text

print(text) # proc