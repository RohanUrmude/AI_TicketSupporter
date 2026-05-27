import React, { useState, useEffect } from 'react';
import './App.css';
import ErrorBoundary from './ErrorBoundary';
import LoadingSpinner from './LoadingSpinner';
import ResultsModal from './ResultsModal';

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT || '/api/ticket';

const PII_PATTERNS = {
    emails: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
    phone_numbers: /(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
    ssn: /(?:\d{3}-\d{2}-\d{4}|\d{9})\b/g,
    credit_cards: /\b(?:\d{4}[-\s]?){3}\d{4}\b/g,
    account_ids: /\b(?:ACC|ACCT|ACCOUNT|CUST|CUSTOMER)[-\s]?[\dA-Z]{6,}\b/gi,
    ip_addresses: /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g,
};

const detectPII = (text) => {
    const detected = {};
    for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
        const matches = text.match(pattern);
        if (matches && matches.length > 0) {
            detected[type] = matches.slice(0, 2);
        }
    }
    return detected;
};

const PIIWarning = ({ detected }) => (
    <div className="pii-warning">
        <div className="pii-warning-icon">⚠️</div>
        <div className="pii-warning-content">
            <strong>Personal Information Detected</strong>
            <ul>
                {Object.entries(detected).map(([type, values]) => (
                    <li key={type}>
                        <span className="pii-type">{type.replace(/_/g, ' ')}:</span> {values.slice(0, 2).join(', ')}
                    </li>
                ))}
            </ul>
        </div>
    </div>
);

const App = () => {
    const [ticketText, setTicketText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');
    const [piiWarning, setPiiWarning] = useState(null);
    const [theme, setTheme] = useState('dark');
    const [charCount, setCharCount] = useState(0);
    const [isListening, setIsListening] = useState(false);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    const handleTextChange = (e) => {
        setTicketText(e.target.value);
        setCharCount(e.target.value.length);
    };

    const startSpeechRecognition = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setError('Speech Recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        let interimTranscript = '';

        recognition.onstart = () => {
            setIsListening(true);
            setError('');
        };

        recognition.onresult = (event) => {
            interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;

                if (event.results[i].isFinal) {
                    setTicketText((prev) => {
                        const newText = prev + (prev ? ' ' : '') + transcript;
                        setCharCount(newText.length);
                        return newText;
                    });
                } else {
                    interimTranscript += transcript;
                }
            }
        };

        recognition.onerror = (event) => {
            setError(`Speech Recognition Error: ${event.error}`);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognition.start();
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!ticketText.trim()) {
            setError('Please enter a ticket description');
            return;
        }

        if (ticketText.length < 10) {
            setError('Ticket description must be at least 10 characters');
            return;
        }

        setIsLoading(true);
        setResults(null);
        setError('');
        setPiiWarning(null);

        const detectedPII = detectPII(ticketText);
        if (Object.keys(detectedPII).length > 0) {
            setIsLoading(false);
            setPiiWarning({
                detected: detectedPII,
                types: Object.keys(detectedPII),
            });
            setError(
                `Security Warning: Your ticket contains ${Object.keys(detectedPII).join(', ')}. Please remove personal information before submitting.`
            );
            return;
        }

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticket_text: ticketText }),
            });

            const data = await response.json();

            if (!response.ok) {
                if (data.warning) {
                    setPiiWarning({
                        detected: data.examples || {},
                        types: data.detected_pii_types || [],
                    });
                    setError(`⚠️ ${data.message}`);
                } else {
                    setError(data.error || 'An error occurred while processing your ticket. Please try again.');
                }
                return;
            }

            setResults(data);
        } catch (err) {
            console.error('Error:', err);
            setError('Unable to reach the server. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ErrorBoundary>
            <div className="app-container">
                <Header theme={theme} setTheme={setTheme} />

                <main className="main-content">
                    <div className="content-wrapper">
                        <section className="input-section">
                            <div className="section-header">
                                <h2>Submit Support Ticket</h2>
                                <p>Describe your issue and our AI will analyze and route it in real-time</p>
                            </div>

                            <form onSubmit={handleSubmit} className="ticket-form">
                                <div className="textarea-wrapper">
                                    <div className="textarea-input-group">
                                        <textarea
                                            value={ticketText}
                                            onChange={handleTextChange}
                                            placeholder="Describe your issue... (e.g., I cannot log in to my account, the app keeps crashing, I was charged twice...)"
                                            disabled={isLoading}
                                            className="ticket-textarea"
                                            minLength="10"
                                            maxLength="5000"
                                        />
                                        <button
                                            type="button"
                                            className={`mic-button ${isListening ? 'listening' : ''}`}
                                            onClick={startSpeechRecognition}
                                            disabled={isLoading || isListening}
                                            title={isListening ? 'Listening...' : 'Click to speak'}
                                        >
                                            {isListening ? '🎤' : '🎙️'}
                                        </button>
                                    </div>
                                    <div className="textarea-footer">
                                        <span className="char-count">{charCount} / 5000</span>
                                        {isListening && <span className="listening-indicator">🔴 Listening...</span>}
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isLoading || !ticketText.trim()}
                                    className="submit-btn"
                                >
                                    <span className="btn-icon">⚡</span>
                                    {isLoading ? (
                                        <>
                                            <span className="spinner"></span>
                                            Processing...
                                        </>
                                    ) : (
                                        'Analyze & Route'
                                    )}
                                </button>
                            </form>

                            {error && (
                                <div className="alert alert-error">
                                    <div className="alert-icon">❌</div>
                                    <div className="alert-content">
                                        <p>{error}</p>
                                        {piiWarning && piiWarning.types.length > 0 && (
                                            <PIIWarning detected={piiWarning.detected} />
                                        )}
                                    </div>
                                </div>
                            )}
                        </section>

                        {isLoading && (
                            <section className="loading-section">
                                <LoadingSpinner message="Analyzing ticket with AI..." />
                            </section>
                        )}

                        {results && !isLoading && (
                            <ResultsModal
                                data={results}
                                onClose={() => {
                                    setResults(null);
                                    setTicketText('');
                                    setCharCount(0);
                                }}
                            />
                        )}
                    </div>

                    {!results && !isLoading && !error && (
                        <section className="info-section">
                            <InfoCards />
                        </section>
                    )}
                </main>

                <Footer />
            </div>
        </ErrorBoundary>
    );
};

const Header = ({ theme, setTheme }) => (
    <header className="app-header">
        <div className="header-content">
            <div className="logo-section">
                <div className="logo-icon">🤖</div>
                <div className="logo-text">
                    <h1>AI Ticket Router</h1>
                    <p>Intelligent Support Ticket Analysis</p>
                </div>
            </div>
            <button
                className="theme-toggle"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                title="Toggle theme"
            >
                {theme === 'dark' ? '☀️' : '🌙'}
            </button>
        </div>
    </header>
);

const InfoCards = () => (
    <div className="info-cards-grid">
        <InfoCard
            icon="⚡"
            title="Real-Time Analysis"
            description="Instant ticket classification and routing"
        />
        <InfoCard
            icon="🎯"
            title="Smart Routing"
            description="Automatic team assignment based on urgency"
        />
        <InfoCard
            icon="💡"
            title="AI Guidance"
            description="Automated troubleshooting steps generated"
        />
        <InfoCard
            icon="📧"
            title="Professional Emails"
            description="Auto-generated customer response templates"
        />
    </div>
);

const InfoCard = ({ icon, title, description }) => (
    <div className="info-card">
        <div className="info-card-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
);

const Footer = () => (
    <footer className="app-footer">
        <p>Powered by BART, Mistral, Llama-2, and Llama-3.1 AI Models</p>
        <p className="footer-meta">Real-time support ticket intelligence platform</p>
    </footer>
);

const AnalysisCard = ({ icon, label, value, color }) => (
    <div className={`analysis-card ${color}`}>
        <div className="analysis-icon">{icon}</div>
        <div className="analysis-details">
            <span className="analysis-label">{label}</span>
            <span className="analysis-value">{value}</span>
        </div>
    </div>
);

const QualityScore = ({ label, score }) => (
    <div className="quality-item">
        <span className="quality-label">{label}</span>
        <div className="quality-bar">
            <div
                className="quality-fill"
                style={{ width: `${(score / 10) * 100}%` }}
            ></div>
        </div>
        <span className="quality-score">{score}/10</span>
    </div>
);

const GuidanceSteps = ({ guidance }) => {
    const steps = guidance
        .split('\n')
        .filter(line => /^\d+\./.test(line.trim()))
        .map((line, idx) => ({
            number: idx + 1,
            text: line.replace(/^\d+\.\s*/, '').trim()
        }));

    return (
        <div className="guidance-steps">
            {steps.map(step => (
                <div key={step.number} className="step-item">
                    <div className="step-number">{step.number}</div>
                    <p>{step.text}</p>
                </div>
            ))}
        </div>
    );
};

const ResultsDisplay = ({ data }) => {
    const getCategoryColor = (category) => {
        const colors = {
            'Technical Problem': 'category-technical',
            'Billing Issue': 'category-billing',
            'Account Access': 'category-account',
            'Product Question': 'category-product',
            'General Inquiry': 'category-general'
        };
        return colors[category] || 'category-general';
    };

    const getUrgencyColor = (urgency) => {
        const colors = {
            'Urgent': 'urgency-urgent',
            'High': 'urgency-high',
            'Medium': 'urgency-medium',
            'Low': 'urgency-low'
        };
        return colors[urgency] || 'urgency-medium';
    };

    return (
        <div className="results-container">
            {/* Ticket ID */}
            <div className="ticket-id-badge">
                Ticket ID: <strong>#{data.ticket_id}</strong>
            </div>

            {/* Analysis Section */}
            <div className="result-card">
                <h3 className="result-title">📊 Ticket Analysis</h3>
                <div className="analysis-grid">
                    <AnalysisCard
                        icon="📁"
                        label="Category"
                        value={data.analysis.category}
                        color={getCategoryColor(data.analysis.category)}
                    />
                    <AnalysisCard
                        icon="⚡"
                        label="Urgency"
                        value={data.analysis.urgency}
                        color={getUrgencyColor(data.analysis.urgency)}
                    />
                    <AnalysisCard
                        icon="😊"
                        label="Sentiment"
                        value={data.analysis.sentiment}
                        color={`sentiment-${data.analysis.sentiment.toLowerCase()}`}
                    />
                </div>
            </div>

            {/* Routing Section */}
            <div className="result-card">
                <h3 className="result-title">🔀 Routing Decision</h3>
                <div className="routing-box">
                    <span className="routing-label">Assigned To</span>
                    <span className="routing-value">{data.routing.decision}</span>
                </div>
            </div>

            {/* Guidance Section */}
            <div className="result-card">
                <h3 className="result-title">🛠️ {data.agent_guidance.type}</h3>
                <GuidanceSteps guidance={data.agent_guidance.guidance} />
            </div>

            {/* Email Section */}
            <div className="result-card">
                <h3 className="result-title">📧 Customer Response</h3>
                <div className="email-preview">
                    <div className="email-preview-content">
                        {data.customer_response.email_preview}
                    </div>
                </div>
            </div>

            {/* Quality Assessment */}
            <div className="result-card">
                <h3 className="result-title">⭐ Quality Assessment</h3>
                <div className="quality-grid">
                    <QualityScore
                        label="Analysis Quality"
                        score={data.quality_assessment.analysis_quality.quality_score}
                    />
                    <QualityScore
                        label="Guidance Quality"
                        score={data.quality_assessment.guidance_quality.quality_score}
                    />
                    <QualityScore
                        label="Email Quality"
                        score={data.quality_assessment.email_quality.quality_score}
                    />
                </div>
            </div>

            {/* Models Used */}
            <div className="result-card models-card">
                <h3 className="result-title">🤖 AI Models Used</h3>
                <div className="models-grid">
                    <ModelBadge label="Analysis" model={data.models_used.analysis} />
                    <ModelBadge label="Guidance" model={data.models_used.guidance} />
                    <ModelBadge label="Email" model={data.models_used.email} />
                    <ModelBadge label="Judge" model={data.models_used.judge} />
                </div>
            </div>
        </div>
    );
};

const ModelBadge = ({ label, model }) => (
    <div className="model-badge">
        <span className="model-label">{label}</span>
        <span className="model-name">{model}</span>
    </div>
);

export default App;
