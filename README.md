# Installation and Instruction

This is a small tool which will scrape article and title data
from the Guardian, Mail and Metro news websites for articles from
todays news. It will then using a bit of natural language processing
provide a relevant summary of that title and article and export
the data to a PDF.

## Installation

The following libraries are required to be installed before the tool
can be used.

1) Beautiful soup - pip install beautifulsoup4
2) Request - pip install requests
3) NLTK Toolkit - pip install nltk
4) Composer - composer require dompdf/dompdf

To run the file - run php -S localhost:port (replacing port
with whatever port you want to run it on) in the command line.
Then click on the link and add /homepage.html to the end of the
link and navigate there where you will see the home page.

You can then make your selections - this will produce a PDF document
in the web browser and also save it to the place where you ran the 
script from.
