"""
Script to set up the database: create tables and populate with sample data
"""
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Set up the database URL directly
os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# Import after environment setup
from app import app, db
from models import User, ResearchPaper, Patent, Note

def setup_database():
    print("Setting up database...")
    
    # Create database tables
    print("Creating database tables...")
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
        # Create a test user if doesn't exist
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
        else:
            print("Test user already exists.")
        
        # Sample research papers
        if ResearchPaper.query.count() == 0:
            papers = [
                {
                    "title": "Advances in Natural Language Processing for Scientific Research",
                    "authors": "Smith, J.; Johnson, A.; Williams, T.",
                    "publication": "Journal of AI and Machine Learning",
                    "year": 2023,
                    "doi": "10.1234/jaiml.2023.56789",
                    "url": "https://example.com/advances-nlp-scientific-research",
                    "abstract": """
                    This paper presents recent advances in natural language processing (NLP) techniques 
                    for scientific research applications. We explore transformer-based models optimized 
                    for scientific text, methods for improved citation analysis, and automated research 
                    summarization systems. Experimental results demonstrate that domain-specific fine-tuning 
                    significantly enhances performance on scientific literature tasks compared to general-purpose 
                    language models. We propose a novel architecture that combines attention mechanisms with 
                    citation graph information to better capture the relationships between scientific concepts.
                    Our approach achieves state-of-the-art results on SciDocs and PubMed benchmarks.
                    """.strip(),
                    "keywords": "NLP, machine learning, scientific text mining, transformers",
                    "user_id": test_user.id
                },
                {
                    "title": "Quantum Computing Approaches to Drug Discovery",
                    "authors": "Chen, L.; Patel, R.; Garcia, M.",
                    "publication": "Computational Chemistry Research",
                    "year": 2024,
                    "doi": "10.5678/ccr.2024.12345",
                    "url": "https://example.com/quantum-computing-drug-discovery",
                    "abstract": """
                    This paper investigates the application of quantum computing algorithms to accelerate 
                    drug discovery processes. We demonstrate how quantum techniques can be used to simulate 
                    molecular interactions and protein folding with significantly higher efficiency than 
                    classical computing methods. Our implementation on current NISQ (Noisy Intermediate-Scale 
                    Quantum) devices shows promising results for small molecules, while our hybrid 
                    quantum-classical approach scales to more complex biological systems. We provide 
                    case studies on several candidate compounds for treatment of neurodegenerative diseases.
                    """.strip(),
                    "keywords": "quantum computing, drug discovery, molecular modeling, NISQ",
                    "user_id": test_user.id
                },
                {
                    "title": "Climate Change Impacts on Global Agricultural Systems",
                    "authors": "Brown, S.; Nguyen, H.; Mehta, P.",
                    "publication": "Environmental Science & Policy",
                    "year": 2023,
                    "doi": "10.9876/esp.2023.54321",
                    "url": "https://example.com/climate-change-agriculture",
                    "abstract": """
                    This comprehensive study analyzes the impacts of climate change on global agricultural 
                    systems through 2050. Using advanced climate models combined with agricultural productivity 
                    data from 195 countries, we project region-specific changes in crop yields, growing seasons, 
                    and water availability. Our findings indicate that while some northern regions may experience 
                    increased productivity, tropical and subtropical agricultural systems face significant challenges. 
                    We propose adaptive strategies including crop diversification, water management technologies, 
                    and policy frameworks to enhance food security in vulnerable regions.
                    """.strip(),
                    "keywords": "climate change, agriculture, food security, adaptation strategies",
                    "user_id": test_user.id
                },
                {
                    "title": "Neural Interfaces for Cognitive Enhancement: Ethical Considerations",
                    "authors": "Martinez, D.; Kim, J.; Anderson, E.",
                    "publication": "Journal of Neuroethics",
                    "year": 2024,
                    "doi": "10.2468/jne.2024.13579",
                    "url": "https://example.com/neural-interfaces-ethics",
                    "abstract": """
                    As neural interface technologies advance toward cognitive enhancement applications, 
                    this paper examines the ethical implications for individuals and society. We analyze 
                    four generations of neural interface technologies, from non-invasive external devices 
                    to emerging integrated neural lace systems. Our framework evaluates concerns related to 
                    autonomy, identity, privacy, equity of access, and potential social stratification. 
                    We propose a set of ethical guidelines for research, development, and regulation of 
                    cognitive enhancement technologies based on principles of responsible innovation, 
                    transparency, and inclusivity.
                    """.strip(),
                    "keywords": "neural interfaces, cognitive enhancement, neuroethics, autonomy",
                    "user_id": test_user.id
                },
                {
                    "title": "Blockchain Solutions for Supply Chain Transparency",
                    "authors": "Taylor, R.; Gupta, A.; Okafor, C.",
                    "publication": "International Journal of Logistics Management",
                    "year": 2023,
                    "doi": "10.3691/ijlm.2023.24680",
                    "url": "https://example.com/blockchain-supply-chain",
                    "abstract": """
                    This research explores blockchain-based solutions for enhancing transparency in global 
                    supply chains. We present a distributed ledger architecture that enables secure, 
                    immutable tracking of products from raw materials to consumer delivery. Our implementation 
                    includes smart contracts for automated compliance verification and consensus mechanisms 
                    optimized for supply chain operations. Case studies in pharmaceutical, food, and electronics 
                    industries demonstrate significant improvements in traceability, counterfeiting prevention, 
                    and regulatory compliance. The proposed framework addresses key challenges including 
                    scalability, integration with IoT devices, and interoperability between blockchain platforms.
                    """.strip(),
                    "keywords": "blockchain, supply chain, transparency, smart contracts",
                    "user_id": test_user.id
                }
            ]
            
            # Add research papers
            for paper_data in papers:
                paper = ResearchPaper(**paper_data)
                db.session.add(paper)
            
            db.session.commit()
            print(f"Added {len(papers)} sample research papers")
        else:
            print("Research papers already exist in the database.")
        
        # Sample patents
        if Patent.query.count() == 0:
            patents = [
                {
                    "title": "Method and System for Real-time Natural Language Processing",
                    "patent_number": "US10123456B2",
                    "inventors": "Zhang, W.; Peterson, L.",
                    "assignee": "AI Innovations Inc.",
                    "filing_date": datetime.now() - timedelta(days=365*2),
                    "issue_date": datetime.now() - timedelta(days=365),
                    "url": "https://example.com/patent/US10123456B2",
                    "abstract": """
                    A method and system for real-time natural language processing that utilizes a 
                    novel approach to semantic parsing. The invention incorporates a multi-stage 
                    processing pipeline with parallel computation to achieve significantly lower 
                    latency than existing systems while maintaining high accuracy. The system 
                    includes specialized components for domain-specific language understanding and 
                    can be deployed in resource-constrained environments.
                    """.strip(),
                    "claims": """
                    1. A system for real-time natural language processing comprising:
                       a. A tokenization module configured to receive and segment natural language input;
                       b. A parallel processing architecture for simultaneous semantic and syntactic analysis;
                       c. A context-aware disambiguation component utilizing historical interaction data;
                       d. An output generator providing structured representations of processed language.
                    
                    2. The system of claim 1, wherein the parallel processing architecture employs 
                       specialized hardware acceleration for key computational components.
                    """.strip(),
                    "user_id": test_user.id
                },
                {
                    "title": "Advanced Material for High-Efficiency Solar Cells",
                    "patent_number": "US20987654A1",
                    "inventors": "Nakamura, H.; Singh, R.; Mendez, J.",
                    "assignee": "SolarTech Laboratories",
                    "filing_date": datetime.now() - timedelta(days=365*1.5),
                    "issue_date": datetime.now() - timedelta(days=180),
                    "url": "https://example.com/patent/US20987654A1",
                    "abstract": """
                    This invention relates to a novel perovskite-silicon tandem solar cell 
                    architecture with enhanced stability and efficiency. The disclosed material 
                    composition addresses degradation challenges in traditional perovskite cells 
                    while achieving conversion efficiencies exceeding 30%. The manufacturing 
                    process is compatible with existing production lines, enabling cost-effective 
                    scaling.
                    """.strip(),
                    "claims": """
                    1. A tandem solar cell comprising:
                       a. A perovskite top layer with composition A2B'B"X6, wherein A is an organic cation;
                       b. A modified interfacial layer providing enhanced moisture resistance;
                       c. A silicon bottom cell with specialized surface texturing;
                       d. An interconnection scheme minimizing resistance losses between subcells.
                    
                    2. The solar cell of claim 1, wherein the perovskite layer includes dopants 
                       that extend operational stability beyond 25 years under standard conditions.
                    """.strip(),
                    "user_id": test_user.id
                },
                {
                    "title": "Biodegradable Packaging Material Derived from Agricultural Waste",
                    "patent_number": "US30567891C1",
                    "inventors": "O'Connor, F.; Yamamoto, T.",
                    "assignee": "EcoPackage Solutions Ltd.",
                    "filing_date": datetime.now() - timedelta(days=365*3),
                    "issue_date": datetime.now() - timedelta(days=365*2),
                    "url": "https://example.com/patent/US30567891C1",
                    "abstract": """
                    A biodegradable packaging material manufactured from agricultural waste products. 
                    The invention provides a method for processing various crop residues into durable, 
                    water-resistant packaging materials without synthetic additives. The resulting 
                    product offers comparable performance to conventional plastic packaging while 
                    achieving complete biodegradation in both industrial composting and natural 
                    environments within 180 days.
                    """.strip(),
                    "claims": """
                    1. A biodegradable packaging material comprising:
                       a. Processed agricultural waste fibers comprising at least 70% of the composition;
                       b. A natural binding agent derived from plant sources;
                       c. A water-resistant coating produced through an enzymatic treatment process;
                       d. The material having a tensile strength of at least 15 MPa.
                    
                    2. A method for manufacturing the biodegradable packaging material of claim 1 
                       comprising steps of fiber extraction, enzymatic treatment, binding, forming, 
                       and curing.
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
        else:
            print("Patents already exist in the database.")
        
        print("Database setup complete!")

if __name__ == "__main__":
    setup_database()