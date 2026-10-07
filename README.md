# PJ Data Analysis Lab - Final Project

**Identifying Drivers of Employee Satisfaction in Text**  
A comparative analysis of LLM-based and dictionary-based classification of Herzberg's Two-Factor Theory in employee reviews.

---

## Project Overview

This project classifies employee reviews (Kununu and Glassdoor) into Herzberg's 14 two-factor theory categories using three classification approaches:

- **LLM-based** (Gemini 2.5 Flash Lite)
- **Dictionary-based** (rule-based keyword matching with German lemmatization)
- **Human coding** (238 manually coded reviews as gold standard)

Classification quality is evaluated via Cohen's κ against the human gold standard. A cross-platform comparison (Kununu vs. Glassdoor) tests robustness across languages and review platforms.

---

## Repository Structure

```

├── webscraping.ipynb          # Scrapes Kununu reviews
│
├── LLM_classy_kununu.ipynb    # LLM classification of Kununu reviews (German)
├── LLM_classy_glassdoor.ipynb # Cleaning + LLM classification of Glassdoor reviews (English)
├── dict_classy.ipynb          # Dictionary-based classification of Kununu reviews
│
├── human_validation.py        # Script for manual coding (human gold standard)
│
├── descriptives.ipynb         # Descriptive statistics for both datasets
├── analysis.ipynb             # Main analysis: κ, prevalence bias, cross-platform comparison
│
├── submissions/               # Submitted files for the course
│   ├── report.pdf             
│   └── final presentation.pdf       
│
├── reviews_json/              # Raw scraped review data (per company)
└── PJDB.db                    # SQLite database (see below)
```

---

## Database: PJDB.db

| Table | N rows | Description |
|---|---|---|
| `REVIEWS_GER` | 19,370 | Kununu reviews (German, 46 companies) |
| `reviews_clean` | 836,254 | Glassdoor reviews (English only, 428 companies) |
| `llm_proscons_kununu` | 13,649 | LLM classifications — Kununu |
| `lex_proscons_kununu` | 19,370 | Dictionary classifications — Kununu |
| `classifications_llm` | 114,325 | LLM classifications — Glassdoor (subset) |
| `human_validation` | 238 | Manually coded Kununu reviews |

All classification tables share the same schema: one row per review, 28 binary columns (`p_<factor>` for pros, `c_<factor>` for cons).

---

## Notebooks

**`webscraping.ipynb`**  
Scrapes employee reviews from Kununu. Saves raw results to `reviews_json/` and loads them into `REVIEWS_GER`.

**`LLM_classy_kununu.ipynb`**  
Classifies Kununu reviews using the Gemini API. Async batch processing (batch size 20, 30 concurrent requests). Includes a post-processing step that resets all-1 classifications on very short review texts. Results written to `llm_proscons_kununu`.

**`LLM_classy_glassdoor.ipynb`**  
Cleans raw Glassdoor CSV (drops empty rows, filters to English via langdetect, writes to `reviews_clean`), then classifies a subset using the same Gemini setup. Results written to `classifications_llm`.

**`dict_classy.ipynb`**  
Dictionary-based classification using a manually curated German keyword lexicon and spaCy lemmatization (`de_core_news_sm`). Results written to `lex_proscons_kununu`.

**`human_validation.py`**  
Command-line tool for manually coding reviews. Loads a random Kununu review, shows pros and cons, and prompts for binary labels per factor. Results saved to `human_validation`.

**`descriptives.ipynb`**  
Descriptive statistics for both datasets: review counts, rating distributions, text lengths, temporal coverage, company breakdown.

**`analysis.ipynb`**  
Main analysis notebook:
1. Cohen's κ: LLM vs. human and Dictionary vs. human (12 factors with ≥ 10 human-coded instances)
2. Prevalence bias: systematic over-/underestimation relative to human coding
3. Cross-platform comparison: Kununu vs. Glassdoor factor prevalences (Spearman ρ)


---

## Reference for Glassdoor Data:

Gauthier, D. (2024). Glassdoor job reviews [Datensatz]. Kaggle. https://www.kaggle.com/datasets/davidgauthier/glassdoor-job-reviews-2