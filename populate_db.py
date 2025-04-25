"""
Script to populate the database with sample research papers and patents
"""
import os
from datetime import datetime, timedelta
from flask_login import current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, ResearchPaper, Patent, Note

# Initialize database with sample data
def populate_database():
    print("Starting database population...")
    
    # Create test user if doesn't exist
    test_user = User.query.filter_by(username="testuser").first()
    if not test_user:
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(test_user)
        db.session.commit()
        print("Created test user: testuser / password123")
    
    # Force repopulation of papers
    print("Removing existing papers...")
    ResearchPaper.query.delete()
    db.session.commit()
    print("Existing papers removed.")
    
    # Sample research papers with real DOIs and URLs
    papers = [
        {
            "title": "Attention Is All You Need",
            "authors": "Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A. N.; Kaiser, L.; Polosukhin, I.",
            "publication": "Advances in Neural Information Processing Systems",
            "year": 2017,
            "doi": "10.48550/arXiv.1706.03762",
            "url": "https://arxiv.org/abs/1706.03762",
            "abstract": """
            The dominant sequence transduction models are based on complex recurrent or convolutional neural networks
            that include an encoder and a decoder. The best performing models also connect the encoder and decoder 
            through an attention mechanism. We propose a new simple network architecture, the Transformer, 
            based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. 
            Experiments on two machine translation tasks show these models to be superior in quality while 
            being more parallelizable and requiring significantly less time to train.
            """.strip(),
            "keywords": "transformers, attention mechanism, neural networks, NLP, machine translation",
            "user_id": test_user.id
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": "Devlin, J.; Chang, M.W.; Lee, K.; Toutanova, K.",
            "publication": "Proceedings of NAACL-HLT 2019",
            "year": 2019,
            "doi": "10.48550/arXiv.1810.04805",
            "url": "https://arxiv.org/abs/1810.04805",
            "abstract": """
            We introduce a new language representation model called BERT, which stands for Bidirectional Encoder 
            Representations from Transformers. Unlike recent language representation models, BERT is designed to 
            pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left 
            and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just 
            one additional output layer to create state-of-the-art models for a wide range of tasks.
            """.strip(),
            "keywords": "BERT, transformers, NLP, language models, deep learning",
            "user_id": test_user.id
        },
        {
            "title": "Deep Residual Learning for Image Recognition",
            "authors": "He, K.; Zhang, X.; Ren, S.; Sun, J.",
            "publication": "Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition",
            "year": 2016,
            "doi": "10.1109/CVPR.2016.90",
            "url": "https://arxiv.org/abs/1512.03385",
            "abstract": """
            Deeper neural networks are more difficult to train. We present a residual learning framework to ease 
            the training of networks that are substantially deeper than those used previously. We explicitly 
            reformulate the layers as learning residual functions with reference to the layer inputs, instead of 
            learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual 
            networks are easier to optimize, and can gain accuracy from considerably increased depth.
            """.strip(),
            "keywords": "deep learning, residual networks, computer vision, image recognition, CNN",
            "user_id": test_user.id
        },
        {
            "title": "AlphaFold Protein Structure Database: massively expanding the structural coverage of protein-sequence space with high-accuracy models",
            "authors": "Varadi, M.; Anyango, S.; Deshpande, M.; Nair, S.; Natassia, C.; et al.",
            "publication": "Nucleic Acids Research",
            "year": 2022,
            "doi": "10.1093/nar/gkab1061",
            "url": "https://academic.oup.com/nar/article/50/D1/D439/6430488",
            "abstract": """
            The AlphaFold Protein Structure Database (AlphaFold DB, https://alphafold.ebi.ac.uk/) provides open 
            access to protein structure predictions for the human proteome and for the proteomes of 47 other 
            organisms, covering over 500 000 proteins. The structure predictions were created using the AlphaFold v2.0 
            system, which has been shown to produce highly accurate scientific predictions of protein structures.
            """.strip(),
            "keywords": "protein structure, AlphaFold, bioinformatics, deep learning, proteomics",
            "user_id": test_user.id
        },
        {
            "title": "A Survey of Large Language Models",
            "authors": "Zhao, W. X.; Zhou, K.; Li, J.; Tang, T.; Wang, X.; et al.",
            "publication": "AI Open",
            "year": 2023,
            "doi": "10.1016/j.aiopen.2023.11.001",
            "url": "https://arxiv.org/abs/2303.18223",
            "abstract": """
            Large language models (LLMs) have demonstrated remarkable capabilities in various natural language processing 
            tasks, including text generation, conversation, and creative writing, and have also shown potential in more 
            complex reasoning tasks. Their abilities have generated considerable interest among researchers and 
            practitioners. This survey provides a comprehensive review of the rapidly evolving field of LLMs.
            """.strip(),
            "keywords": "large language models, deep learning, NLP, AI, natural language processing",
            "user_id": test_user.id
        }
    ]
    
    # Add research papers
    for paper_data in papers:
        paper = ResearchPaper(**paper_data)
        db.session.add(paper)
    
    db.session.commit()
    print(f"Added {len(papers)} sample research papers")
    
    # Force repopulation of patents
    print("Removing existing patents...")
    Patent.query.delete()
    db.session.commit()
    print("Existing patents removed.")
    
    # Sample patents with real information
    patents = [
        {
            "title": "Processing language using neural networks",
            "patent_number": "US10223439B2",
            "inventors": "Eck, D.; Jaitly, N.; Rifkin, R.",
            "assignee": "Google LLC",
            "filing_date": datetime(2018, 3, 22),
            "issue_date": datetime(2019, 3, 5),
            "url": "https://patents.google.com/patent/US10223439B2",
            "abstract": """
            Systems and techniques for language processing using neural networks are disclosed. 
            A system obtains a sequence of inputs representing a sequence of tokens. The system 
            processes the sequence of inputs using a recurrent neural network (RNN) encoder 
            to generate an encoded representation of the sequence of inputs.
            """.strip(),
            "claims": """
            1. A method performed by one or more computers, the method comprising:
               obtaining a sequence of inputs representing a sequence of tokens;
               processing the sequence of inputs using a recurrent neural network (RNN) encoder to generate an encoded representation of the sequence of inputs.
            """.strip(),
            "user_id": test_user.id
        },
        {
            "title": "Techniques for translating speech to text and vice versa",
            "patent_number": "US11227589B2",
            "inventors": "Vanhoucke, V.; Laurent, A.; Schalkwyk, J.; Miller, D.; Le, Q.",
            "assignee": "Google LLC",
            "filing_date": datetime(2019, 12, 9),
            "issue_date": datetime(2022, 1, 18),
            "url": "https://patents.google.com/patent/US11227589B2",
            "abstract": """
            Methods, systems, and apparatus, including computer programs encoded on a computer storage 
            medium, for generating translations in a target language of spoken language in a source 
            language. In one aspect, a method includes receiving a plurality of audio data samples from 
            a user device in a first language.
            """.strip(),
            "claims": """
            1. A computer-implemented method comprising:
               receiving a plurality of audio data samples from a user device, wherein the plurality of audio data samples represent a user utterance in a first language;
               determining, from the plurality of audio data samples, one or more features based on a representation of the user utterance in the first language.
            """.strip(),
            "user_id": test_user.id
        },
        {
            "title": "Collaborative machine learning model training for distributed systems",
            "patent_number": "US11074065B2",
            "inventors": "McMahan, H. B.; Moore, R.; Sears, J.; Talwar, K.; Zhang, L.",
            "assignee": "Google LLC",
            "filing_date": datetime(2017, 3, 27),
            "issue_date": datetime(2021, 7, 27),
            "url": "https://patents.google.com/patent/US11074065B2",
            "abstract": """
            A method of collaborative machine learning model training for distributed systems is provided. 
            The method includes obtaining training data local to a client computing device, the training 
            data being partitioned from a universal dataset of a plurality of client computing devices.
            """.strip(),
            "claims": """
            1. A method of training a machine learning model by a client computing device, the method comprising:
               obtaining training data local to the client computing device, the training data being partitioned from a universal dataset of a plurality of client computing devices;
               obtaining a machine learning model from a server system, the machine learning model to be updated via a plurality of iterations.
            """.strip(),
            "user_id": test_user.id
        },
    ]
    
    # Add patents
    for patent_data in patents:
        patent = Patent(**patent_data)
        db.session.add(patent)
    
    db.session.commit()
    print(f"Added {len(patents)} sample patents")
    
    print("Database population complete!")

if __name__ == "__main__":
    with app.app_context():
        populate_database()