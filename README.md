# The problem
Importing details into beancount from certain companies can lead to ambiguous classifications, or extra work. 

For instance, if your transaction is from eBay, is it a book, a new coffee table or baby clothes?

It is not useful to classify these all under the same account as it does not give us a true reflection of where our 
money has been spent.

And going through our records, or worse, our memories, is tedious and error-prone.

There must be an easier way to automatically fetch the details from somewhere and augment our imported transactions with
enough information to help us make better informed decisions on which account the spend was made. 

But from where do we get this information?

# A solution
Luckily for us... most companies now email us the details of our orders when we make a purchase. Even cashiers at stores
offer to email us our receipts in order to reduce paper waste. 

So, why not use this information to help us when reconciling our finances?

# What is beancount-import-gmail
beancount-import-gmail is an importer that downloads order details from your gmail mailbox, parsing the relevant data 
and then augmenting your transactions with the order details.

It turns something like

~~~beancount
2019-02-03 * "eBay Auction Payment; Napero Shop; Completed"
  time: "22:51:17"
  Assets:PayPal -9.03 GBP
~~~

into 

~~~beancount
2019-02-03 * "eBay Auction Payment; Napero Shop; Completed"
  time: "22:51:17"
  Assets:PayPal       -9.03 GBP
  ReplaceWithAccount   2.52 GBP
    description: "Paw Patrol  Bunting Banner Children's Kids Birthday Party Decorations    142864983558"
  ReplaceWithAccount   4.59 GBP
    description: "10 pcs Paw Patrol themed Happy Birthday Party Bags Loot Bag Decoration    142988326565"
  ReplaceWithAccount   1.92 GBP
~~~

It has been written as a framework which allows you to write your own email parsers to handle emails from the companies 
that are important to you.

# How does it work
beancount-import-gmail uses the gmail API to access your mailbox using OAuth, pulling in the emails the parser has been
configured to search for.

The HTML of the emails is then extracted and passed to the appropriate parser as a BeautifulSoup. 

Your parser is then responsible for extracting out the purchase details, totals and postage and packaging details and 
returning a list of Receipts. 

The Receipts are then matched against your transactions where new legs are added with descriptions of the spend.


# How to install
pip install https://github.com/kubauk/beancount-import-gmail.git

## Requirements
beancount-import-gmail requires 
- beancount 3.x
- beangulp

# How to configure
Configuration is done in one of two methods either as a delegate importer or a decorator.

### Credentials
In order to use the gmail API you need to have an account on [Google Cloud Platform](https://console.cloud.google.com/)
where you need to create and then download API credentials, as well as enable gmail API access.

Summary instructions can be found on [Stack Overflow](https://stackoverflow.com/questions/58026765/how-to-download-credentials-json-in-gmail-api-enable-java).

## Delegate configuration
Simply pass your importer into the beancount-import-gmail importer

```python
gmail_import = beancount_gmail.GmailImporter(FancyImporter(), 
                                             UKeBayParser(), 
                                             "Expenses:YourPostageAccount",
                                             "youremail@gmail.com",
                                             "/path/to/folder_containing_credentials")
```

## Decorator configuration
Simply decorate the extract method of your importer with as many beancount-import-gmails configurations as you would 
like and the will all be called in turn to augment the transactions retrieved by your importer.

```python
class FancyImporter(beangulp.Importer):
  @gmail_import(UKeBayParser(), 
                "youremail@gmail.com", 
                "/path/to/folder_containing_credentials", 
                "Expenses:YourPostageAccount")
  def extract(self, filepath: str, existing_entries: data.Entries) -> data.Entries:
    # ... Importer code ...
    return transactions
```

# Supported parsers
Given I am based in the UK, my importers are biased to institutions based here. Also, the framework does not support 
currencies other than the British Pound. My intention is decouple my parsers from this project into their own project 
and have it support all currencies.
- UK PayPal 
- UK eBay
- Whichever one you care to write

# Todo
- Support other email hosts. This will likely fork a new gmail agnostic project.
- Support all currencies
- This framework should parser agnostic and specific parsers should be in their own project.


