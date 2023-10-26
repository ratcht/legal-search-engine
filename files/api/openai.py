import openai
import tiktoken
import logging
from files.obj.searchobj import SearchObj


def authenticate(API_KEY, ORGANIZATION):
  openai.organization =  ORGANIZATION# organization name
  openai.api_key = API_KEY


def create_embedding(embedding_model: str, content):
  """Create an embedding"""
  try:
    response = openai.Embedding.create(model=embedding_model, input=content)
  except Exception as e:
    print(e)
    raise e

  
  for i, be in enumerate(response["data"]):
    assert i == be["index"]  # double check embeddings are in same order as input

  return response

def format_completion(dict):
  formatted = [
    {"role": "user", "content": dict["prompt"]},
    {"role": "assistant", "content": dict["response"]},
  ]
  return formatted

def previous_example():
  query = """Use the provided excerpts, including the title of the document, to answer the subsequent question. Make sure your answer is concise. Do not give answers that are too long. If a direct answer cannot be found in the information, try to give a broader answer based on all the excerpts provided, referring to knowledge of Pakistani Law.
Document Title: The Constitution of Pakistan.pdf. Excerpt:
CONSTITUTION OF PAKISTAN (In the name of Allah, the most Beneficent, the most Merciful.) THE CONSTITUTION OF THE ISLAMIC REPUBLIC OF PAKISTAN [12TH APRIL, 1973] Preamble Whereas sovereignty over the entire Universe belongs to Almighty Allah alone, and the authority to be exercised by the people of Pakistan within the limits prescribed by Him is a sacred trust; And whereas it is the will of the people of Pakistan to establish an order; Wherein the State shall exercise its powers and authority through the chosen representatives of the people; Wherein the principles of democracy, freedom, equality, tolerance and social justice, as enunciated by Islam, shall be fully observed; Wherein the Muslims shall be enabled to order their lives in the individual and collective spheres in accordance with the teachings and requirements of Islam as set out in the Holy Quran and Sunnah; Wherein adequate provision shall be made for the minorities freely to profess and practise their religions and develop their cultures; Wherein the territories now included in or in accession with Pakistan and such other territories as may hereafter be included in or accede to Pakistan shall form a Federation wherein the units will be autonomous with such boundaries and limitations on their powers and authority as may be prescribed; Wherein shall be guaranteed fundamental rights, including equality of status, of opportunity and before law, social, economic and political justice, and freedom of thought, expression, belief, faith, worship and association, subject to law and public morality; Wherein adequate provision shall be made to safeguard the legitimate interests of minorities and backward and depressed classes; Wherein the independence of the judiciary shall be fully secured; 

1 Document Title: The Constitution of Pakistan.pdf. Excerpt:
CONSTITUTION OF PAKISTAN Wherein the integrity of the territories of the Federation, its independence and all its rights, including its sovereign rights on land, sea and air, shall be safeguarded; So that the people of Pakistan may prosper and attain their rightful and honoured place amongst the nations of the World and make their full contribution towards international peace and progress and happiness of humanity; Now, therefore, we, the people of Pakistan; Conscious of our responsibility before Almighty Allah and men; Cognisant of the sacrifices made by the people in the cause of Pakistan; Faithful to the declaration made by the Founder of Pakistan, Quaid-i-Azam Mohammad Ali Jinnah, that Pakistan would be a democratic State based on Islamic principles of social justice; Dedicated to the preservation of democracy achieved by the unremitting struggle of the people against oppression and tyranny; Inspired by the resolve to protect our national and political unity and solidarity by creating an egalitarian society through a new order; Do hereby, through our representatives in the National Assembly, adopt, enact and give to ourselves, this Constitution. ______________

2 Document Title: The Constitution of Pakistan.pdf. Excerpt: 
CONSTITUTION OF PAKISTAN PART I Introductory 1. The Republic and its territories 11. (1) Pakistan shall be Federal Republic to be known as the Islamic Republic of Pakistan, hereinafter referred to as Pakistan. 2[(2) The territories of Pakistan shall comprise\\u2014 (a) the Provinces of 3[Balochistan], the 4[Khyber Pakhtunkhwa], the Punjab and 5[Sindh]; (b) the Islamabad Capital Territory, hereinafter referred to as the Federal Capital; 6[and] 6[(c) * * * * * *] 6[(c)] such States and territories as are or may be included in Pakistan, whether by accession or otherwise. (3) 7[Majlis-e-Shoora (Parliament)] may by law admit into the Federation new States or areas on such terms and conditions as it thinks fit.] 2. Islam to be State religion 2. Islam shall be the State religion of Pakistan. 2A. The Objectives Resolution to form part of substantive provisions 8[2A. The principles and provisions set out in the Objectives Resolution reproduced in the Annex are hereby made substantive part of the Constitution and shall have effect accordingly]. 1 The provisions of the Constitution except those of Articles 6, 8 to 28, (both inclusive), clauses 2 and (2a) of Article 101, Articles 199, 213 to 216 (both inclusive) and 270-A, brought into force with effect from 10th March, 1985, ride S.R.O. No. 212(I)/85. dated 10th March, 1985, Gazette of Pakistan, Extraordinary, Part-II, page 279 and the aforesaid Articles brought into force with effect from 30th December, 1985, vide S.R.O. No. 1273(I)/85 dated 29th December. 1985, Gazette of Pakistan, Extraordinary, Part-I1, page 3185. 2 Subs. by the Constitution (First Amdt.) Act, 1974 (33 of 1974), s. 2, for \\"clauses (2), (3) and (4)\\" (w.e.f; the 4th May, 1974). 3 Subs. By the Constitution (Eighteenth Amdt.) Act, 2010 (10 of 2010), s. 3 for \\u201cBalochistan.\\u201d 4 Subs. ibid., for \\u201cNorth-West-Frontier\\u201d. 5 Subs. ibid., for \\u201cSindh\\u201d. 6 Amended by the Constitution (Twenty-fifth Amdt.) Act, 2018 (37 of 2018), s. 2. w.e.f. 31-05-2018. 7 Subs. by the Revival of the Constitution of 1973 Order, 1985 (P.O. No. 14 of 1985), Art. 2 and Sch., for \\"Parliament\\". 8 New Article 2A Ins. Ibid.

3 Document Title: The Constitution of Pakistan.pdf. Excerpt: 
CONSTITUTION OF PAKISTAN 1[ANNEX (Article 2A) The Objectives Resolution (In the name of Allah, the most beneficent, the most merciful.) Whereas sovereignty over the entire universe belongs to Allah Almighty alone and the authority which He has delegated to the State of Pakistan, through its people for being exercised within the limits prescribed by Him is a sacred trust; This Constituent Assembly representing the people of Pakistan resolves to frame a constitution for the sovereign independent State of Pakistan; Wherein the State shall exercise its powers and authority through the chosen representatives of the people; Wherein the principles of democracy, freedom, equality, tolerance and social justice as enunciated by Islam shall be fully observed; Wherein the Muslims shall be enabled to order their lives in the individual and collective spheres in accordance with the teachings and requirements of Islam as set-out in the Holy Quran and the Sunnah; Wherein adequate provision shall be made for the minorities to 2[freely] profess and practise their religions and develop their cultures; Wherein the territories now included in or in accession with Pakistan and such other territories as may hereafter be included in or accede to Pakistan shall form a Federation wherein the units will be autonomous with such boundaries and limitations on their powers and authority as may be prescribed; Wherein shall be guaranteed fundamental rights including equality of status, of opportunity and before law, social, economic and political justice, and freedom of thought, expression, belief, faith, worship and association, subject to law and public morality; 1 New Annex ins. by P.O. No. 14 of 1985, Art. 2 and Sch. 2 Ins. by the Constitution (Eighteenth Amdt.) Act, 2010 (10 of 2010), s. 99. 177 
Question: What is the preamble of the Constitution of Pakistan, and what fundamental principles does it lay out?
"""

  response = """The preamble of the Constitution of Pakistan is a concise and profound introductory statement that outlines the foundational principles, values, and aspirations upon which the Constitution is built. It serves as a guiding framework for the entire constitutional structure and reflects the collective will and vision of the people of Pakistan.

Fundamental Principles Mentioned in the Preamble:

The sovereignty of Allah: The preamble emphasizes the sovereignty of Allah as the ultimate source of authority, highlighting the Islamic identity of Pakistan and its commitment to establishing a society based on Islamic principles.

Democratic System: The preamble underscores Pakistan's commitment to democracy, acknowledging the people's right to choose their government through a democratic process. It emphasizes the importance of representative institutions and governance by the people.

Islamic Way of Life: The preamble reflects the aspiration to enable the people of Pakistan to lead their lives in accordance with Islamic values, ethics, and teachings. It aims to establish a society that upholds the principles of justice, equality, and social welfare as guided by Islam.

Equality and Social Justice: The preamble emphasizes the pursuit of equality and social justice, striving to eliminate disparities and ensure a just and fair society for all citizens, regardless of their backgrounds.

Human Dignity and Rights: The preamble recognizes the inherent dignity and fundamental rights of individuals, aiming to protect and promote their rights and freedoms within the framework of Islamic teachings and democratic principles.

Rule of Law: The preamble upholds the supremacy of the constitution and the rule of law, ensuring that all state actions are governed by the principles and norms outlined in the constitution.

Unity and Integration: The preamble seeks to foster national unity and integration among the diverse people of Pakistan, transcending regional, linguistic, and cultural differences.

Interfaith Harmony: The preamble acknowledges the importance of interfaith harmony and respect for the rights and beliefs of religious minorities, promoting a tolerant and inclusive society.

Dignity of Labor: The preamble recognizes the significance of labor and the role of workers in the progress and development of the country, emphasizing their rights and contributions.

Good Governance: The preamble expresses the intent to establish good governance, transparency, and accountability in all spheres of public life.

In conclusion, the preamble of the Constitution of Pakistan serves as a declaration of the nation's fundamental principles, encapsulating the core values of Islam, democracy, equality, social justice, human rights, and the rule of law. It provides a roadmap for the development of a just, progressive, and harmonious society while upholding the country's Islamic heritage and democratic aspirations.
"""
  formatted = [
    {"role": "user", "content": query},
    {"role": "assistant", "content": response},
  ]
  return formatted

def query(message: str, model: str):
  context = previous_example()




  messages = [
    {"role": "system", "content": "You are skilled at reading and interpreting documents. You will throughly process provided documents and answer detailed questions given the information provided. You also follow past conversations and can answer questions about previous questions."},
    *context,
    {"role": "user", "content": message},
  ]
  print(messages)

  try:
    response = openai.ChatCompletion.create(
      model=model,
      messages=messages,
      temperature=0
    )
  except Exception as e:
    raise Exception(f"From Chat Completion... {e}")
  
  response_message = response["choices"][0]["message"]["content"]
  return response_message

async def aquery(message: str, model: str) -> str:
  context = previous_example()

  while True:
    logging.info("Running async query...")
    messages = [
      {"role": "system", "content": "You are skilled at reading and interpreting documents. You will throughly process provided documents and answer detailed questions given the information provided."},
      *context,
      {"role": "user", "content": message},
    ]

    response = await openai.ChatCompletion.acreate(
      model=model,
      messages=messages,
      temperature=0
    )

    response_message = response["choices"][0]["message"]["content"]
    return response_message

def num_tokens(text: str, model: str) -> int:
  """Return the number of tokens in a string"""
  encoding = tiktoken.encoding_for_model(model)
  return len(encoding.encode(text))