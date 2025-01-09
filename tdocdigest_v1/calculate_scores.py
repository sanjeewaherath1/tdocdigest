"""
This file calculate the score for the generated summary compared to original text
"""
import logging
import openai
import os

# from bert_score import score


# Calculate the score (semantic) using the summary with gpt model
def calculate_semantic_score(tdocsummarytxt, tdoctxt, userkey, model):
    """
    Generate a semantic score for the given abstractive summary. Prompt specifies the score style
    :param tdocsummarytxt: summary text
    :param tdoctxt: original long text
    :param userkey: API key for gpt-4o
    :param model: openai model (gpt-4o)
    :return: Score in the following format
                Relevance: [score]/10
                Coherence: [score]/10
                Completeness: [score]/10
                Conciseness: [score]/10
                Overall: [score]/10
    """
    # openai.api_key = userkey
    openai.api_key = os.getenv("OPENAI_API_KEY")

    logging.info(f'Calculate semantic score')
    # Rating prompt for OpenAI API
    prompt = f""" Given the following original text and its generated summary, please evaluate the quality of the 
    summary based on four criteria: relevance, coherence, completeness, and conciseness. For each criterion, 
    provide a rating from 1 to 10, with 10 being the best. Then, give an overall rating.

      Original Text:
      {tdoctxt}

      Generated Summary:
      {tdocsummarytxt}

      Provide your response in the following format:
      Relevance: [score]/10
      Coherence: [score]/10
      Completeness: [score]/10
      Conciseness: [score]/10
      Overall: [score]/10
  """
    err = ''
    ratingsummary = ''

    try:
        # Send the prompt to OpenAI API
        response_summary_rating = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],  # the messages format
            temperature=0.01  # Set to a low temperature for more consistent ratings
        )

        # Extract the response content
        ratingsummary = response_summary_rating.choices[0].message.content
        # log the message
        logging.info(f'Rating summary {ratingsummary}')

        return ratingsummary, err

    except Exception as e:
        err = str(e)
        logging.error(f"OpenAI API returned an error: {err}")
        if "authentication" in err.lower():
            err = f"Authentication failed. Check your API key. {err}"
            logging.error(err)
        if "rate limit" in err.lower():
            err = f"Rate limit exceeded. Try again later. {err}"
            logging.error(err)
        if "invalid" in err.lower():
            err = f"The request was invalid. Check your parameters. {err}"
            logging.error(err)
        else:
            err = f"An unexpected OpenAI error occurred.{err}"
            logging.error(err)

        return ratingsummary, err


# Compute the BERT score
def calculate_bert_score(tdoc_summary_txt, tdoc_txt):
    # Calculate BERTScore
    P, R, F1 = score([tdoc_txt], [tdoc_summary_txt], lang="en", model_type="bert-base-uncased")

    # Log BERTScore results
    p_mean = P.mean().item()
    r_mean = R.mean().item()
    f1_mean = F1.mean().item()

    logging.info(f"Precision:{p_mean}, Recall: {r_mean}, F1 Score: {f1_mean}")

    return p_mean, r_mean, f1_mean
