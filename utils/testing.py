if __name__ == "__main__":
    sample_text = """
    Name of the Company: Bharti Airtel Ltd
    Category: Super Dream Internship / Placement
    Date of Visit: Will be announced later
    Eligible Branches: B. Tech. CSE IT & related
    Eligibility Criteria: % in X and XII – 90% or 9.0 CGPA; in Pursuing Degree – 90% or 9.0 CGPA; No Standing Arrears
    CTC if converted: 14.75 LPA (12.75 Fixed + 1 JB +1 RB )
    Stipend: 50,000
    Last date for Registration: 8th Oct 2025 (11:00 am)
    Application Source: Google Form
    """

    from .parsing_utils import extract_placement_offer
    from .email_utils import fetch_emails

    result = extract_placement_offer(sample_text)
    print("TEST EXTRACTION RESULT:")
    for key, value in result.items():
        print(f"{key}: {value}")