import yfinance as yf
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from app.core.config import settings

# 1. Define Agent Tools
tavily_tool = TavilySearchResults(max_results=4, api_key=settings.TAVILY_API_KEY)

# 2. Define Output Schemas
class FinancialAnalysis(BaseModel):
    """Structured financial analysis of a company."""
    key_metrics: Dict[str, Any] = Field(description="Key financial metrics like P/E Ratio, Debt-to-Equity, Revenue Growth (YoY), etc.")
    recent_performance: str = Field(description="A summary of the company's recent financial performance based on earnings reports and stock price.")

class MarketAnalysis(BaseModel):
    """Structured market analysis of a company."""
    industry_trends: List[str] = Field(description="Major trends in the company's industry.")
    competitive_landscape: str = Field(description="Analysis of key competitors and the company's market position.")
    growth_opportunities: List[str] = Field(description="Potential areas for growth and expansion.")

class FinalReport(BaseModel):
    """Final structured investment report."""
    company_ticker: str
    pros: List[str] = Field(description="A bulleted list of reasons to invest in the company.")
    cons: List[str] = Field(description="A bulleted list of reasons to be cautious about investing.")
    risk_assessment: str = Field(description="A summary of key risks (market, regulatory, operational).")
    final_recommendation: str = Field(description="A final 'Invest' or 'Do Not Invest' verdict.")
    recommendation_summary: str = Field(description="A 1-2 sentence justification for the final recommendation.")

# 3. Define Graph State
class AgentState(TypedDict):
    company_ticker: str
    financial_data: Dict[str, Any]
    news_and_filings: str
    financial_analysis_result: FinancialAnalysis
    market_analysis_result: MarketAnalysis
    final_report: FinalReport

# 4. Define Agent Nodes
def data_collection_node(state: AgentState):
    print("--- AGENT: Data Collector ---")
    ticker = state["company_ticker"]
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = stock.financials
    
    financial_data = {
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "revenue_growth": info.get("revenueGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
        "recent_revenue": financials.loc['Total Revenue'].to_dict() if not financials.empty else {},
    }
    search_results = tavily_tool.invoke(f"latest news and SEC filings for {ticker}")
    news_and_filings = "\n".join([res["content"] for res in search_results])
    
    return {"financial_data": financial_data, "news_and_filings": news_and_filings}

def financial_analyst_node(state: AgentState):
    print("--- AGENT: Financial Analyst ---")
    # llm = ChatOpenAI(model="gpt-4-turbo", openai_api_key=settings.OPENAI_API_KEY)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=settings.GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(FinancialAnalysis)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert financial analyst. Analyze the provided data and generate a structured financial report."),
        ("human", "Here is the financial data for {company_ticker}:\n\n{financial_data}\n\nAnd recent news/filings:\n\n{news_and_filings}\n\nPlease provide your analysis."),
    ])
    chain = prompt | structured_llm
    result = chain.invoke(state)
    return {"financial_analysis_result": result}

def market_analyst_node(state: AgentState):
    print("--- AGENT: Market Analyst ---")
    # llm = ChatOpenAI(model="gpt-4-turbo", openai_api_key=settings.OPENAI_API_KEY)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=settings.GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(MarketAnalysis)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert market analyst. Analyze the company's market position based on recent news and trends."),
        ("human", "Company: {company_ticker}\n\nRecent News:\n\n{news_and_filings}\n\nPlease provide a structured market analysis."),
    ])
    chain = prompt | structured_llm
    result = chain.invoke(state)
    return {"market_analysis_result": result}

def final_advisor_node(state: AgentState):
    print("--- AGENT: Final Advisor ---")
    # llm = ChatOpenAI(model="gpt-4-turbo", openai_api_key=settings.OPENAI_API_KEY)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=settings.GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(FinalReport)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior investment advisor. Synthesize the financial and market analyses to create a final investment report with a clear recommendation."),
        ("human", """
        Company Ticker: {company_ticker}
        Financial Analysis:\n- Key Metrics: {financial_metrics}\n- Performance Summary: {performance_summary}
        Market Analysis:\n- Industry Trends: {industry_trends}\n- Competitive Landscape: {competitive_landscape}
        Based on all this information, generate the final report.
        """),
    ])
    chain = prompt | structured_llm
    financial_analysis = state['financial_analysis_result']
    market_analysis = state['market_analysis_result']
    result = chain.invoke({
        "company_ticker": state['company_ticker'],
        "financial_metrics": financial_analysis.key_metrics,
        "performance_summary": financial_analysis.recent_performance,
        "industry_trends": market_analysis.industry_trends,
        "competitive_landscape": market_analysis.competitive_landscape
    })
    return {"final_report": result}

# 5. Build and Compile the Graph
workflow = StateGraph(AgentState)
workflow.add_node("data_collector", data_collection_node)
workflow.add_node("financial_analyst", financial_analyst_node)
workflow.add_node("market_analyst", market_analyst_node)
workflow.add_node("final_advisor", final_advisor_node)
workflow.set_entry_point("data_collector")
workflow.add_edge("data_collector", "financial_analyst")
workflow.add_edge("data_collector", "market_analyst")
workflow.add_conditional_edges("financial_analyst", lambda state: "final_advisor" if state.get("market_analysis_result") else None)
workflow.add_conditional_edges("market_analyst", lambda state: "final_advisor" if state.get("financial_analysis_result") else None)
workflow.add_edge("final_advisor", END)
app_graph = workflow.compile()

# Main function to run the analysis
def run_analysis(company_ticker: str):
    inputs = {"company_ticker": company_ticker}
    final_state = app_graph.invoke(inputs)
    return final_state['final_report'].dict()