import scrapy
import subprocess
import os
import uuid
import csv
from scrapy.selector import Selector
from AUCTION.auction_item import EPCItem


username = ''
password = ''
eigusername = ''
eigpassword = ''


class SavillsEPCSpider(scrapy.Spider):
    name = 'SavillsEPCSpider'
    allowed_domains = ['auctions.savills.co.uk']
    base_url = 'http://catalogue.auctions.savills.co.uk/'
    start_urls = ['http://catalogue.auctions.savills.co.uk/London-National/Online-Catalogue/']

    def parse(self, response):
        requests = []
        online_catalogue_entries = response.xpath('//table[@id="ctl00_ContentPlaceHolder2_RadGridLotList_ctl00"]/tbody/tr')
        for each_entry in online_catalogue_entries:
            legal_doc_link = each_entry.xpath('td/a/@href').extract().pop()
            legal_doc_link = legal_doc_link.replace('../../', '')
            requests.append(scrapy.Request(self.base_url + legal_doc_link, callback=self.parse_legal_links))
        return requests

    def parse_legal_links(self, response):
        if response.xpath('//div[@id="header_signin_container"]/ul/li/a[@id="LoginView1_hplSignIn"]'):
            # user is not logged in.
            # try to log the user in.
            # self.login(response)
            pass
        # do the rest to track the EPC.


# This became a failure since the data is loaded in an iframe and the page initially has no auction lists.
# On investigation it is understood that the auctin list is populated from
# https://ams.eigroup.co.uk/data/script/auction/414/null
# which is JS code that creates and writes a table in the DOM.
# Need further investigation.
class StrettonsEPCSpider(scrapy.Spider):
    name = 'StrettonsEPCSpider'
    allowed_domains = ['auctions.strettons.co.uk', 'legaldocuments.eigroup.co.uk']
    base_url = 'http://auctions.strettons.co.uk/'
    start_urls = ['http://auctions.strettons.co.uk/currentauction.aspx']

    def parse(self, response):
        return scrapy.Request(response.url, callback=self.parse_again)

    def parse_again(self, response):
        requests = []
        online_catalogue_entries = response.xpath('//div[@class="container"]/table[@class="tablelotlist"]/tbody/tr')
        print online_catalogue_entries.extract()


# this was done for first link which blocked our IP.
# class AuctionHouseEPCSpider(scrapy.Spider):
#     name = 'AuctionHouseEPCSpider'
#     allowed_domains = ['auctioneertemplates.eigroup.co.uk', 'legaldocuments.eigroup.co.uk', 'passport.eigroup.co.uk']
#     base_url = 'http://auctioneertemplates.eigroup.co.uk/'
#     download_base_url = 'https://legaldocuments.eigroup.co.uk/'
#     start_urls = ['http://auctioneertemplates.eigroup.co.uk/guides.aspx?a=680&c=lon']

#     def parse(self, response):
#         requests = []
#         online_catalogue_entries = response.xpath('//table[@class="lot-table"]/tr')
#         for each_entry in online_catalogue_entries:
#             each_link = each_entry.xpath('td/a/@href').extract()
#             if each_link:
#                 requests.append(scrapy.Request(self.base_url + each_link.pop(), callback=self.parse_details_page))
#         return requests

#     def parse_details_page(self, response):
#         legal_doc_link = response.xpath('//table[@class="extra-details"]/tr/td/table//a[@id="HyperLink1"]/@href').extract()
#         self.log('parse_details_page')
#         if len(legal_doc_link) > 0:
#             request = scrapy.Request(legal_doc_link[0], callback=self.check_login, dont_filter=True)
#             request.meta['legal_doc_link'] = legal_doc_link[0]
#             return request

#     def check_login(self, response):
#         if len(response.xpath('//input[@id="ButtonSignIn"]').extract()) > 0:
#             self.log('Going to login.')
#             request = scrapy.FormRequest.from_response(
#                 response,
#                 formdata={'Email': username, 'Password': password},
#                 callback=self.parse_eig
#             )
#             return request
#         else:
#             self.log('Already logged in.')
#             return self.parse_eig(response)

#     def parse_eig(self, response):
#         self.log('Login success. Going to parse EIG site for EPC.')
#         epc_download_link = response.xpath('//table[@class="DownloadGroup"]//a[re:test(text(), "([eE][pP][cC]|[eE]nergy).*\.pdf")]/@href').extract()
#         if len(epc_download_link) > 0:
#             self.log('An epc document found. Going to download it.')
#             request = scrapy.Request(self.download_base_url + epc_download_link[0], callback=self.save_pdf)
#             request.meta['file_name'] = epc_download_link[0]
#             return request

#     def save_pdf(self, response):
#         f = open('%s.pdf' % response.meta['file_name'], 'wb+')
#         f.write(response.body)
#         try:
#             subprocess('python pdf2txt.py -t html %s' % (f.name))
#         except Exception as e:
#             self.log('Could not parse pdf to html. Error is %s.' % e)
#         f.close()


class AuctionHouseEPCSpider2(scrapy.Spider):
    name = 'AuctionHouseEPCSpider2'
    auctioneer = 'Auction House'
    allowed_domains = ['eigroup.co.uk', 'legaldocuments.eigroup.co.uk', 'passport.eigroup.co.uk']
    download_base_url = 'https://legaldocuments.eigroup.co.uk/'
    start_urls = ['https://www.eigroup.co.uk/clients/auctions/fulldetails.aspx?auctionid=22414']

    def parse(self, response):
        if len(response.xpath('//input[@id="Content_ButtonLogin"]').extract()) > 0:
            self.log('Going to login.')
            request = scrapy.FormRequest.from_response(
                response,
                formdata={'ctl00$Content$TextBoxUsername': eigusername, 'ctl00$Content$TextBoxPassword': eigpassword},
                callback=self.parse_details_page
            )
            return request
        else:
            self.log('Already logged in.')
            return self.parse_details_page(response)

    def parse_details_page(self, response):
        requests = []
        online_catalogue_entries = response.xpath('//table[re:test(@id, "ListViewLots_ClientPropertyControl\d+_\d+_FormViewLot_\d+")]')
        for each_entry in online_catalogue_entries:
            lot_number = None
            each_p_tag = each_entry.xpath('tr/td/table[@class="table-search-result"]/tr/td/table/tr/td/p')
            for a_p_tag in each_p_tag:
                if len(a_p_tag.xpath('b[contains(text(), "Lot Number")]').extract()) > 0:
                    lot_number = a_p_tag.xpath('text()').re(r'.(\d+).')
                    break
            legal_link = each_entry.xpath('tr/td/table[@class="table-search-result"]/tr/th/a[re:test(@href, "https://legaldocuments.eigroup.co.uk/default.aspx\?lotid=\d")]')
            if legal_link:
                redirect_link = legal_link.xpath('@href').extract().pop()
                self.log('Going to redirect to %s.' % str(redirect_link))
                request = scrapy.Request(redirect_link, callback=self.check_login)
                self.log('Lot number found is %s.' % lot_number)
                request.meta['lot_number'] = lot_number
                requests.append(request)
        return requests

    def check_login(self, response):
        if len(response.xpath('//input[@id="ButtonSignIn"]').extract()) > 0:
            self.log('Going to login in passport.')
            request = scrapy.FormRequest.from_response(
                response,
                formdata={'Email': username, 'Password': password},
                callback=self.parse_eig,
                dont_filter=True
            )
            return request
        else:
            self.log('Already logged in passport.')
            return self.parse_eig(response)

    def parse_eig(self, response):
        self.log('Login success. Going to parse EIG site for EPC.')
        epc_download_link = response.xpath('//table[@class="DownloadGroup"]//a[re:test(text(), "([eE][pP][cC]|[eE]nergy).*\.pdf")]/@href').extract()
        if len(epc_download_link) > 0:
            self.log('An epc document found. Going to download it.')
            request = scrapy.Request(self.download_base_url + epc_download_link[0], callback=self.save_pdf)
            request.meta['file_name'] = epc_download_link[0]
            request.meta['lot_number'] = response.meta['lot_number']
            return request
        return

    def save_pdf(self, response):
        file_name = response.meta['file_name'].replace('?', '_')
        file_name = file_name.replace('&', '_')
        file_name = file_name.replace('.', '_')
        f = open('%s.pdf' % file_name, 'wb+')
        f.write(response.body)
        f.close()
        self.log('Going to convert %s.' % os.path.abspath(f.name))
        pdf2html = document_to_html(os.path.abspath(f.name))
        html_selector = Selector(text=pdf2html)
        self.log(html_selector)
        self.log('Finding the floor area using superscript re.')
        unicode_re = u'(\d+).m\xc2\xb2'
        floor_area = html_selector.xpath('//p/text()').re(unicode_re)
        self.log('Floor area found is %s.' % floor_area)
        self.log('Writing to csv file.')
        if len(floor_area) > 0:
            item = EPCItem()
            item['auctioneer'] = self.auctioneer
            item['lot_number'] = response.meta['lot_number'][0]
            item['floor_area'] = floor_area.pop()
            yield item


class BarnardMarcusEPCSpider(scrapy.Spider):
    name = 'BarnardMarcusEPCSpider'
    auctioneer = 'Barnard Marcus'
    allowed_domains = ['auctioneertemplates.eigroup.co.uk', 'legaldocuments.eigroup.co.uk', 'passport.eigroup.co.uk']
    base_url = 'http://auctioneertemplates.eigroup.co.uk/'
    download_base_url = 'https://legaldocuments.eigroup.co.uk/'
    start_urls = ['http://auctioneertemplates.eigroup.co.uk/guides.aspx?a=5&c=brn']

    def parse(self, response):
        requests = []
        a_tags = response.xpath('//table[@class="lot-table"]/tr/td/a[re:test(@id, "ListViewGuides_HyperLinkLotNum_\d+")]')
        for each_a_tag in a_tags:
            link = each_a_tag.xpath('@href').extract()
            lot_number = each_a_tag.xpath('text()').extract()
            request = scrapy.Request(self.base_url + link[0], callback=self.parse_each_lot)
            request.meta['lot_number'] = lot_number[0]
        return requests

    def parse_each_lot(self, response):
        self.log(str(response.meta['lot_number']))


def document_to_html(file_path):
    tmp = "/tmp"
    guid = str(uuid.uuid1())
    # convert the file, using a temporary file w/ a random name
    command = "abiword -t %(tmp)s/%(guid)s.html %(file_path)s; cat %(tmp)s/%(guid)s.html" % locals()
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    error = p.stderr.readlines()
    if error:
        raise Exception("".join(error))
    html = p.stdout.readlines()
    return "".join(html).decode('latin_1').encode('utf-8')
