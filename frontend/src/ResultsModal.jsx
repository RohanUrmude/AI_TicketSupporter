import React, { useState, useEffect } from 'react';

const ResultsModal = ({ data, onClose }) => {
    const [isVisible, setIsVisible] = useState(true);
    const [selectedLanguage, setSelectedLanguage] = useState('English');

    const handleClose = () => {
        setIsVisible(false);
        setTimeout(onClose, 300);
    };

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
        <>
            {/* Backdrop */}
            <div
                className={`results-backdrop ${isVisible ? 'visible' : 'hidden'}`}
                onClick={handleClose}
            ></div>

            {/* Modal Container */}
            <div className={`results-modal ${isVisible ? 'visible' : 'hidden'}`}>
                {/* Close Button */}
                <button
                    className="modal-close-btn"
                    onClick={handleClose}
                    title="Close results"
                >
                    ✕
                </button>

                {/* Modal Content */}
                <div className="modal-content">
                    {/* Header */}
                    <div className="modal-header">
                        <h2>✨ Analysis Complete</h2>
                        <div className="ticket-id-badge-modal">
                            Ticket ID: <strong>#{data.ticket_id}</strong>
                        </div>
                    </div>

                    {/* Analysis Section */}
                    <div className="modal-section analysis-section">
                        <h3>📊 Comprehensive Ticket Analysis</h3>
                        <div className="analysis-grid-modal">
                            <AnalysisCardModal
                                icon="📁"
                                label="Category"
                                value={data.analysis.category}
                                color={getCategoryColor(data.analysis.category)}
                            />
                            <AnalysisCardModal
                                icon="⚡"
                                label="Urgency"
                                value={data.analysis.urgency}
                                color={getUrgencyColor(data.analysis.urgency)}
                            />
                            <AnalysisCardModal
                                icon="😊"
                                label="Sentiment"
                                value={data.analysis.sentiment}
                                color={`sentiment-${data.analysis.sentiment.toLowerCase()}`}
                            />
                            {data.analysis.complexity && (
                                <AnalysisCardModal
                                    icon="🔧"
                                    label="Complexity"
                                    value={data.analysis.complexity}
                                    color="analysis-card"
                                />
                            )}
                            {data.analysis.issue_severity && (
                                <AnalysisCardModal
                                    icon="🚨"
                                    label="Severity"
                                    value={data.analysis.issue_severity}
                                    color="analysis-card"
                                />
                            )}
                            {data.analysis.customer_emotion && (
                                <AnalysisCardModal
                                    icon="💭"
                                    label="Emotion"
                                    value={data.analysis.customer_emotion}
                                    color="analysis-card"
                                />
                            )}
                        </div>

                        {/* Extended Analysis Details */}
                        <div className="extended-analysis-grid">
                            {data.analysis.resolution_type && (
                                <ExtendedAnalysisItem
                                    label="Resolution"
                                    value={data.analysis.resolution_type}
                                />
                            )}
                            {data.analysis.issue_type && (
                                <ExtendedAnalysisItem
                                    label="Issue Type"
                                    value={data.analysis.issue_type}
                                />
                            )}
                            {data.analysis.business_impact && (
                                <ExtendedAnalysisItem
                                    label="Business Impact"
                                    value={data.analysis.business_impact}
                                />
                            )}
                            {data.analysis.time_sensitivity && (
                                <ExtendedAnalysisItem
                                    label="Time Sensitivity"
                                    value={data.analysis.time_sensitivity}
                                />
                            )}
                            {data.analysis.escalation_needed && (
                                <ExtendedAnalysisItem
                                    label="Escalation"
                                    value={data.analysis.escalation_needed}
                                />
                            )}
                            {data.analysis.human_intervention && (
                                <ExtendedAnalysisItem
                                    label="Handling"
                                    value={data.analysis.human_intervention}
                                />
                            )}
                            {data.analysis.impact_scope && (
                                <ExtendedAnalysisItem
                                    label="Impact Scope"
                                    value={data.analysis.impact_scope}
                                />
                            )}
                            {data.analysis.customer_emotion && (
                                <ExtendedAnalysisItem
                                    label="Customer Emotion"
                                    value={data.analysis.customer_emotion}
                                />
                            )}
                            {data.analysis.issue_severity && (
                                <ExtendedAnalysisItem
                                    label="Severity"
                                    value={data.analysis.issue_severity}
                                />
                            )}
                        </div>
                    </div>

                    {/* Routing Section */}
                    <div className="modal-section routing-section">
                        <h3>🔀 Routing Decision</h3>
                        <div className="routing-box-modal">
                            <span className="routing-label">Assigned To</span>
                            <span className="routing-value-modal">{data.routing.decision}</span>
                        </div>
                    </div>

                    {/* Guidance Section */}
                    <div className="modal-section guidance-section">
                        <h3>🛠️ {data.agent_guidance.type}</h3>
                        <GuidanceStepsModal
                            guidance={data.agent_guidance.guidance}
                            selectedLanguage={selectedLanguage}
                            onLanguageChange={setSelectedLanguage}
                        />
                    </div>

                    {/* Email Section */}
                    <div className="modal-section email-section">
                        <h3>📧 Customer Response Email</h3>
                        <EmailSectionModal
                            emailText={data.customer_response.email_preview}
                            selectedLanguage={selectedLanguage}
                        />
                    </div>

                    {/* Quality Assessment */}
                    <div className="modal-section quality-section">
                        <h3>⭐ Quality Assessment</h3>
                        <div className="quality-grid-modal">
                            <QualityScoreModal
                                label="Analysis Quality"
                                score={data.quality_assessment.analysis_quality.quality_score}
                            />
                            <QualityScoreModal
                                label="Guidance Quality"
                                score={data.quality_assessment.guidance_quality.quality_score}
                            />
                            <QualityScoreModal
                                label="Email Quality"
                                score={data.quality_assessment.email_quality.quality_score}
                            />
                        </div>
                    </div>

                    {/* Models Used */}
                    <div className="modal-section models-section">
                        <h3>🤖 AI Models Used</h3>
                        <div className="models-grid-modal">
                            <ModelBadgeModal label="Analysis" model={data.models_used.analysis} />
                            <ModelBadgeModal label="Guidance" model={data.models_used.guidance} />
                            <ModelBadgeModal label="Email" model={data.models_used.email} />
                            <ModelBadgeModal label="Judge" model={data.models_used.judge} />
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="modal-footer">
                        <button className="modal-action-btn close-btn" onClick={handleClose}>
                            ← Back to Form
                        </button>
                        <button className="modal-action-btn" onClick={() => window.print()}>
                            🖨️ Print Results
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
};

const AnalysisCardModal = ({ icon, label, value, color }) => (
    <div className={`analysis-card-modal ${color}`}>
        <div className="analysis-icon-modal">{icon}</div>
        <div className="analysis-details-modal">
            <span className="analysis-label-modal">{label}</span>
            <span className="analysis-value-modal">{value}</span>
        </div>
    </div>
);

const QualityScoreModal = ({ label, score }) => (
    <div className="quality-item-modal">
        <span className="quality-label-modal">{label}</span>
        <div className="quality-bar-modal">
            <div
                className="quality-fill-modal"
                style={{ width: `${(score / 10) * 100}%` }}
            ></div>
        </div>
        <span className="quality-score-modal">{score}/10</span>
    </div>
);

const GuidanceStepsModal = ({ guidance, selectedLanguage, onLanguageChange }) => {
    const [translatedGuidance, setTranslatedGuidance] = React.useState(guidance);
    const [isTranslating, setIsTranslating] = React.useState(false);

    const INDIAN_LANGUAGES = [
        { code: 'English', name: 'English', nativeName: 'English' },
        { code: 'Hindi', name: 'Hindi', nativeName: 'हिंदी' },
        { code: 'Tamil', name: 'Tamil', nativeName: 'தமிழ்' },
        { code: 'Telugu', name: 'Telugu', nativeName: 'తెలుగు' },
        { code: 'Kannada', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
        { code: 'Malayalam', name: 'Malayalam', nativeName: 'മലയാളം' },
        { code: 'Gujarati', name: 'Gujarati', nativeName: 'ગુજરાતી' },
        { code: 'Marathi', name: 'Marathi', nativeName: 'मराठी' },
        { code: 'Bengali', name: 'Bengali', nativeName: 'বাংলা' },
        { code: 'Punjabi', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
    ];

    const handleLanguageChange = async (lang) => {
        onLanguageChange(lang);

        if (lang === 'English') {
            setTranslatedGuidance(guidance);
            return;
        }

        setIsTranslating(true);

        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: guidance, target_language: lang })
            });

            if (response.ok) {
                const data = await response.json();
                setTranslatedGuidance(data.translated_text);
            } else {
                setTranslatedGuidance(guidance);
            }
        } catch (error) {
            console.error('Translation error:', error);
            setTranslatedGuidance(guidance);
        } finally {
            setIsTranslating(false);
        }
    };

    const steps = translatedGuidance
        .split('\n')
        .filter(line => /^\d+\./.test(line.trim()))
        .map((line, idx) => ({
            number: idx + 1,
            text: line.replace(/^\d+\.\s*/, '').trim()
        }));

    return (
        <div className="guidance-container-modal">
            <div className="language-selector-modal">
                <label className="language-label-modal">🌐 Select Language:</label>
                <select
                    className="language-dropdown-modal"
                    value={selectedLanguage}
                    onChange={(e) => handleLanguageChange(e.target.value)}
                    disabled={isTranslating}
                >
                    {INDIAN_LANGUAGES.map(lang => (
                        <option key={lang.code} value={lang.code}>
                            {lang.nativeName} ({lang.code})
                        </option>
                    ))}
                </select>
            </div>

            <div className="guidance-steps-modal">
                {isTranslating && (
                    <div className="translation-loading">
                        <span className="spinner-small"></span> Translating...
                    </div>
                )}
                {steps.map(step => (
                    <div key={step.number} className="step-item-modal">
                        <div className="step-number-modal">{step.number}</div>
                        <p>{step.text}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

const ModelBadgeModal = ({ label, model }) => (
    <div className="model-badge-modal">
        <span className="model-label-modal">{label}</span>
        <span className="model-name-modal">{model}</span>
    </div>
);

const ExtendedAnalysisItem = ({ label, value }) => (
    <div className="extended-analysis-item">
        <span className="extended-label">{label}</span>
        <span className="extended-value">{value}</span>
    </div>
);

const EmailSectionModal = ({ emailText, selectedLanguage }) => {
    const [translatedEmail, setTranslatedEmail] = React.useState(emailText);
    const [isTranslating, setIsTranslating] = React.useState(false);

    React.useEffect(() => {
        if (selectedLanguage === 'English') {
            setTranslatedEmail(emailText);
            return;
        }

        const translateEmail = async () => {
            setIsTranslating(true);
            try {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: emailText, target_language: selectedLanguage })
                });

                if (response.ok) {
                    const data = await response.json();
                    setTranslatedEmail(data.translated_text);
                } else {
                    setTranslatedEmail(emailText);
                }
            } catch (error) {
                console.error('Email translation error:', error);
                setTranslatedEmail(emailText);
            } finally {
                setIsTranslating(false);
            }
        };

        translateEmail();
    }, [selectedLanguage, emailText]);

    return (
        <div className="email-container-modal">
            {isTranslating && (
                <div className="translation-loading">
                    <span className="spinner-small"></span> Translating email...
                </div>
            )}
            <div className="email-header-modal">
                <div className="email-from">
                    <span className="email-label">From:</span>
                    <span>Support Team</span>
                </div>
                <div className="email-subject">
                    <span className="email-label">Subject:</span>
                    <span>Support Ticket Confirmation & Next Steps</span>
                </div>
            </div>
            <div className="email-body-modal">
                {translatedEmail}
            </div>
            <div className="email-footer-modal">
                <button className="copy-email-btn" onClick={() => {
                    navigator.clipboard.writeText(translatedEmail);
                    alert('Email copied to clipboard!');
                }}>
                    📋 Copy Email
                </button>
            </div>
        </div>
    );
};

export default ResultsModal;
