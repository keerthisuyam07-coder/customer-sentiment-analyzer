
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import io
from collections import Counter
from textblob import TextBlob
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet


# =========================================
# 1. PAGE CONFIGURATION
# =========================================

st.set_page_config(
    page_title="Customer Sentiment Analyzer",
    page_icon="📊",
    layout="wide"
)


# =========================================
# 2. SENTIMENT ANALYSIS
# =========================================

def analyze_sentiment(text):

    if pd.isna(text) or str(text).strip() == "":
        return 0.0, 0.0, "Neutral"

    analysis = TextBlob(str(text))

    polarity = analysis.sentiment.polarity
    subjectivity = analysis.sentiment.subjectivity

    if polarity > 0.1:
        sentiment = "Positive"
    elif polarity < -0.1:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return polarity, subjectivity, sentiment


# =========================================
# 3. KEYWORD EXTRACTION
# =========================================

def extract_keywords(reviews):

    stop_words = {
        "the", "and", "was", "is", "are", "this",
        "that", "with", "for", "but", "very", "have",
        "has", "had", "you", "your", "from", "they",
        "them", "not", "its", "it", "the", "a", "an",
        "to", "of", "in", "on", "my", "i", "we",
        "our", "be", "as", "at", "or", "so",
        "product", "were", "been", "would", "could",
        "should", "will", "can", "all", "one",
        "when", "what", "which", "there", "their",
        "also", "after", "very", "just", "than"
    }

    words = []

    for review in reviews.dropna():

        tokens = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            str(review).lower()
        )

        words.extend(
            word for word in tokens
            if word not in stop_words
        )

    return Counter(words).most_common(10)


# =========================================
# 4. PDF REPORT GENERATION
# =========================================

def generate_pdf_report(df):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    total = len(df)

    positive = (df["Sentiment"] == "Positive").sum()
    negative = (df["Sentiment"] == "Negative").sum()
    neutral = (df["Sentiment"] == "Neutral").sum()

    avg_polarity = df["Polarity"].mean() if total else 0
    avg_subjectivity = df["Subjectivity"].mean() if total else 0

    satisfaction = (avg_polarity + 1) * 50

    elements.append(
        Paragraph(
            "Customer Sentiment Analysis Report",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Customer Feedback Summary",
            styles["Heading2"]
        )
    )

    data = [
        ["Metric", "Result"],
        ["Total Reviews", str(total)],
        ["Positive Reviews", str(positive)],
        ["Negative Reviews", str(negative)],
        ["Neutral Reviews", str(neutral)],
        [
            "Positive Percentage",
            f"{positive / total * 100:.1f}%" if total else "0%"
        ],
        [
            "Negative Percentage",
            f"{negative / total * 100:.1f}%" if total else "0%"
        ],
        [
            "Neutral Percentage",
            f"{neutral / total * 100:.1f}%" if total else "0%"
        ],
        ["Average Polarity", f"{avg_polarity:.2f}"],
        ["Average Subjectivity", f"{avg_subjectivity:.2f}"],
        ["Sentiment-based Indicator", f"{satisfaction:.1f}/100"]
    ]

    table = Table(
        data,
        colWidths=[250, 220]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.darkblue
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.whitesmoke
            )
        ])
    )

    elements.append(table)

    elements.append(Spacer(1, 25))

    elements.append(
        Paragraph(
            "Generated by Customer Sentiment Analyzer",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Note: The satisfaction indicator is estimated "
            "from average sentiment polarity. It is not a "
            "direct customer satisfaction survey score.",
            styles["Italic"]
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================
# 5. MAIN APPLICATION
# =========================================

st.title("📊 Customer Sentiment Analyzer")

st.write(
    "Analyze customer reviews, identify positive and "
    "negative feedback, discover useful keywords, "
    "and generate downloadable reports."
)


# =========================================
# 6. APPLICATION TABS
# =========================================

tab1, tab2 = st.tabs([
    "📝 Single Text Analysis",
    "📁 Bulk CSV Analysis"
])


# =========================================
# 7. SINGLE REVIEW ANALYSIS
# =========================================

with tab1:

    st.subheader("Analyze Individual Customer Review")

    user_input = st.text_area(
        "Enter customer review:",
        placeholder=(
            "The product is excellent "
            "and delivery was fast!"
        )
    )

    if st.button(
        "Analyze Review",
        type="primary",
        key="single_analysis"
    ):

        if user_input.strip():

            score, subjectivity, label = analyze_sentiment(
                user_input
            )

            col1, col2, col3 = st.columns(3)

            col1.metric("Sentiment", label)
            col2.metric("Polarity", f"{score:.2f}")
            col3.metric("Subjectivity", f"{subjectivity:.2f}")

            if label == "Positive":
                st.success("😊 Positive customer feedback!")

            elif label == "Negative":
                st.error("😞 Negative customer feedback!")

            else:
                st.info("😐 Neutral customer feedback!")

        else:
            st.warning("Please enter a customer review.")


# =========================================
# 8. BULK CSV ANALYSIS
# =========================================

with tab2:

    st.subheader("Bulk Customer Review Analysis")

    st.caption(
        "Upload a CSV file containing customer reviews."
    )

    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=["csv"],
        key="csv_upload"
    )

    if uploaded_file is not None:

        try:

            # Read CSV with encoding fallback
            file_bytes = uploaded_file.getvalue()

            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding="utf-8-sig"
                )
            except UnicodeDecodeError:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding="cp1252"
                )

            if df.empty or len(df.columns) == 0:

                st.error("The uploaded CSV file is empty.")

            else:

                st.success("CSV uploaded successfully!")

                st.write("Preview of uploaded data:")

                st.dataframe(
                    df.head(),
                    use_container_width=True
                )

                # Find likely review column
                default_index = 0

                for i, col in enumerate(df.columns):

                    if str(col).strip().lower() in [
                        "review",
                        "text",
                        "reviews",
                        "feedback",
                        "comment"
                    ]:
                        default_index = i
                        break

                column_name = st.selectbox(
                    "Select review column:",
                    df.columns,
                    index=default_index,
                    key="review_column"
                )

                # Unique upload signature
                import hashlib

                file_signature = hashlib.md5(
                    file_bytes
                ).hexdigest()

                # Run batch analysis
                if st.button(
                    "Run Batch Analysis",
                    type="primary",
                    key="batch_analysis"
                ):

                    valid_reviews = (
                        df[column_name]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )

                    if not valid_reviews.ne("").any():

                        st.warning(
                            "No customer reviews found "
                            "in the selected column."
                        )

                    else:

                        result_df = df.copy()

                        results = result_df[
                            column_name
                        ].apply(analyze_sentiment)

                        result_df["Polarity"] = results.apply(
                            lambda x: x[0]
                        )

                        result_df["Subjectivity"] = results.apply(
                            lambda x: x[1]
                        )

                        result_df["Sentiment"] = results.apply(
                            lambda x: x[2]
                        )

                        # Store results
                        st.session_state["analysis_results"] = (
                            result_df
                        )

                        st.session_state["analysis_signature"] = (
                            file_signature
                        )

                        st.session_state["analysis_column"] = (
                            column_name
                        )

                # =================================
                # 9. DISPLAY ANALYSIS RESULTS
                # =================================

                if (
                    "analysis_results" in st.session_state
                    and st.session_state.get(
                        "analysis_signature"
                    ) == file_signature
                    and st.session_state.get(
                        "analysis_column"
                    ) == column_name
                ):

                    # IMPORTANT:
                    # result_df is defined here.
                    # All dashboard and report code stays
                    # inside this block.

                    result_df = st.session_state[
                        "analysis_results"
                    ]

                    total = len(result_df)

                    positive = (
                        result_df["Sentiment"] == "Positive"
                    ).sum()

                    negative = (
                        result_df["Sentiment"] == "Negative"
                    ).sum()

                    neutral = (
                        result_df["Sentiment"] == "Neutral"
                    ).sum()

                    # =================================
                    # 10. SENTIMENT DASHBOARD
                    # =================================

                    st.divider()

                    st.subheader("📊 Sentiment Dashboard")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric("Total Reviews", total)
                    col2.metric("😊 Positive", positive)
                    col3.metric("😞 Negative", negative)
                    col4.metric("😐 Neutral", neutral)

                    # =================================
                    # 11. SENTIMENT PERCENTAGES
                    # =================================

                    st.subheader("Sentiment Percentages")

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Positive %",
                        f"{positive / total * 100:.1f}%"
                        if total else "0%"
                    )

                    col2.metric(
                        "Negative %",
                        f"{negative / total * 100:.1f}%"
                        if total else "0%"
                    )

                    col3.metric(
                        "Neutral %",
                        f"{neutral / total * 100:.1f}%"
                        if total else "0%"
                    )

                    # =================================
                    # 12. SENTIMENT CHARTS
                    # =================================

                    st.divider()

                    st.subheader(
                        "📈 Sentiment Visualizations"
                    )

                    counts = (
                        result_df["Sentiment"]
                        .value_counts()
                        .reindex(
                            ["Positive", "Negative", "Neutral"],
                            fill_value=0
                        )
                        .rename_axis("Sentiment")
                        .reset_index(name="Count")
                    )

                    chart1, chart2 = st.columns(2)

                    with chart1:

                        fig1 = px.pie(
                            counts,
                            names="Sentiment",
                            values="Count",
                            title="Sentiment Distribution",
                            color="Sentiment",
                            color_discrete_map={
                                "Positive": "#00CC96",
                                "Negative": "#EF553B",
                                "Neutral": "#636EFA"
                            },
                            hole=0.35
                        )

                        st.plotly_chart(
                            fig1,
                            use_container_width=True
                        )

                    with chart2:

                        fig2 = px.bar(
                            counts,
                            x="Sentiment",
                            y="Count",
                            color="Sentiment",
                            title="Sentiment Comparison",
                            text="Count",
                            color_discrete_map={
                                "Positive": "#00CC96",
                                "Negative": "#EF553B",
                                "Neutral": "#636EFA"
                            }
                        )

                        st.plotly_chart(
                            fig2,
                            use_container_width=True
                        )

                    # =================================
                    # 13. OVERALL ANALYSIS
                    # =================================

                    st.divider()

                    st.subheader("📌 Overall Analysis")

                    avg_polarity = (
                        result_df["Polarity"].mean()
                        if total else 0
                    )

                    avg_subjectivity = (
                        result_df["Subjectivity"].mean()
                        if total else 0
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Average Polarity",
                        f"{avg_polarity:.2f}"
                    )

                    col2.metric(
                        "Average Subjectivity",
                        f"{avg_subjectivity:.2f}"
                    )

                    # =================================
                    # 14. CUSTOMER SATISFACTION
                    # =================================

                    st.divider()

                    st.subheader(
                        "⭐ Customer Satisfaction Indicator"
                    )

                    satisfaction_score = (
                        avg_polarity + 1
                    ) * 50

                    st.metric(
                        "Sentiment-based Satisfaction Indicator",
                        f"{satisfaction_score:.1f}/100"
                    )

                    st.progress(
                        min(
                            max(
                                satisfaction_score / 100,
                                0.0
                            ),
                            1.0
                        )
                    )

                    st.caption(
                        "This is an estimated indicator based "
                        "on sentiment polarity, not a direct "
                        "customer satisfaction survey score."
                    )

                    # =================================
                    # 15. FILTER CUSTOMER REVIEWS
                    # =================================

                    st.divider()

                    st.subheader(
                        "🔍 Filter Customer Reviews"
                    )

                    selected = st.selectbox(
                        "Choose sentiment:",
                        [
                            "All",
                            "Positive",
                            "Negative",
                            "Neutral"
                        ],
                        key="sentiment_filter"
                    )

                    if selected == "All":
                        filtered_df = result_df
                    else:
                        filtered_df = result_df[
                            result_df["Sentiment"] == selected
                        ]

                    st.dataframe(
                        filtered_df,
                        use_container_width=True
                    )

                    st.write(
                        f"Showing {len(filtered_df)} reviews."
                    )

                    # =================================
                    # 16. CUSTOMER FEEDBACK INSIGHTS
                    # =================================

                    st.divider()

                    st.header(
                        "💡 Customer Feedback Insights"
                    )

                    positive_reviews = result_df[
                        result_df["Sentiment"] == "Positive"
                    ][column_name]

                    negative_reviews = result_df[
                        result_df["Sentiment"] == "Negative"
                    ][column_name]

                    positive_words = extract_keywords(
                        positive_reviews
                    )

                    negative_words = extract_keywords(
                        negative_reviews
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        st.subheader(
                            "😊 Positive Feedback Keywords"
                        )

                        if positive_words:

                            positive_df = pd.DataFrame(
                                positive_words,
                                columns=["Keyword", "Frequency"]
                            )

                            st.dataframe(
                                positive_df,
                                use_container_width=True
                            )

                            fig_positive = px.bar(
                                positive_df,
                                x="Frequency",
                                y="Keyword",
                                orientation="h",
                                title="Positive Feedback"
                            )

                            st.plotly_chart(
                                fig_positive,
                                use_container_width=True
                            )

                        else:

                            st.info(
                                "No positive keywords found."
                            )

                    with col2:

                        st.subheader(
                            "😞 Negative Feedback Keywords"
                        )

                        if negative_words:

                            negative_df = pd.DataFrame(
                                negative_words,
                                columns=["Keyword", "Frequency"]
                            )

                            st.dataframe(
                                negative_df,
                                use_container_width=True
                            )

                            fig_negative = px.bar(
                                negative_df,
                                x="Frequency",
                                y="Keyword",
                                orientation="h",
                                title="Negative Feedback"
                            )

                            st.plotly_chart(
                                fig_negative,
                                use_container_width=True
                            )

                        else:

                            st.info(
                                "No negative keywords found."
                            )

                    st.success(
                        "Customer feedback analysis completed!"
                    )

                    # =================================
                    # 17. CSV DOWNLOAD
                    # =================================

                    st.divider()

                    st.subheader(
                        "📥 Download Analysis Reports"
                    )

                    csv_data = result_df.to_csv(
                        index=False
                    ).encode("utf-8-sig")

                    st.download_button(
                        "📥 Download Complete Results CSV",
                        data=csv_data,
                        file_name="sentiment_results.csv",
                        mime="text/csv"
                    )

                    # =================================
                    # 18. PDF DOWNLOAD
                    # =================================

                    pdf_data = generate_pdf_report(
                        result_df
                    )

                    st.download_button(
                        "📄 Download Professional PDF Report",
                        data=pdf_data,
                        file_name="customer_sentiment_report.pdf",
                        mime="application/pdf"
                    )

        except Exception as e:

            st.error(
                f"Unable to process CSV: {e}"
            )

    else:

        st.info(
            "Upload a CSV file to begin bulk sentiment analysis."
        )


# =========================================
# 19. APPLICATION FOOTER
# =========================================

st.divider()

st.caption(
    "Customer Sentiment Analyzer | "
    "Built with Python, Streamlit, TextBlob, "
    "Pandas, Plotly and ReportLab."
)
