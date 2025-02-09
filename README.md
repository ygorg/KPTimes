# 📰 KPTimes Corpus

* **Update 09/02/205** : Adding link to the [huggingface dataset repository](https://huggingface.co/datasets/taln-ls2n/kptimes)
* **Update 17/01/2020** : Adding download links for minimal version

## Download links

Please download the dataset from our huggingface repository.
* [https://huggingface.co/datasets/taln-ls2n/kptimes](https://huggingface.co/datasets/taln-ls2n/kptimes)


## Data fields

The name of the fields were chosen to match [KP20k](https://github.com/memray/seq2seq-keyphrase#data).

* **id** : unique identifier for the document
* **date** : publishing date (YYYY/MM/DD)
* **author** : author of the article (`<meta name="author"/>`)
* **categories** : categories of the article (1 or 2 categories)
* **title** : title of the document (`<meta property="og:title"/>`)
* **headline** : self-explanatory (`<meta property="og:description"/>`)
* **abstract** : content of the article
* **keyword** : list of keywords (`<meta name="keywords"/>`)
* **file_name** : last part of the url, **this is not a primary key**
* **url** : original url of the document


## Retrieving the dataset

```sh
cd scripts
sh download.sh # This should take 34 hours !
python3 to_jsonl.py -f ../train.url.filelist
python3 to_jsonl.py -f ../valid.url.filelist
python3 to_jsonl.py -f ../test_JPTimes.url.filelist
python3 to_jsonl.py -f ../test_NYTimes.url.filelist
```


## File Description

- `test.urls.filelist` - Test Document urls and ids
- `train.urls.filelist` - Train Document urls and ids
- `valid.urls.filelist` - Validation Document urls and ids

- `download.sh` - Script to download document in html format
- `to_jsonl.py` - Script to convert html document to jsonl format

`.url.filelist` - tsv file with 2 columns, the first is the id of the document in this dataset, the second is the url of the document

`.jsonl` - a file where each line is a valid json object


## Using the dataset

Loading `.jsonl` file:

```python
import json
with open('test.jsonl') as f:
    data = [json.loads(line) for line in f]
```

Converting keyword field to lists:
```python
# keeping variants information
keyphrases = [[v for v in kw.split(',')] for kw in keyword.split(';')]
# flattening the list
keyphrases = [v for kw in keyword.split(';') for v in kw.split(',')]
```


## Inquiries

If you find problems in the dataset, please use file an Issue or contact ygor.gallina [at] univ-nantes.fr.

## License

See [LICENCE](https://github.com/ygorg/KPTimes/blob/master/LICENSE). Please note that the documents were extracted from [NYTimes](https://www.nytimes.com/) and [JPTimes](https://www.japantimes.co.jp/) and are their property.

## Citation

Gallina, Ygor, Florian Boudin, and Béatrice Daille.
KPTimes: A Large-Scale Dataset for Keyphrase Generation on News Documents."
Proceedings of the 12th [International Conference on Natural Language Generation](https://www.inlg2019.com/). 2019.

```
@inproceedings{gallina2019kptimes,
  title={KPTimes: A Large-Scale Dataset for Keyphrase Generation on News Documents},
  author={Gallina, Ygor and Boudin, Florian and Daille, B{\'e}atrice},
  booktitle={Proceedings of the 12th International Conference on Natural Language Generation},
  pages={130--135},
  year={2019}
}
```
