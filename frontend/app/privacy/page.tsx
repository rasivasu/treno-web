import React from 'react';

export default function PrivacyPolicy() {
    return (
        <main className="max-w-3xl mx-auto px-6 py-12 prose prose-slate">
            <h1 className="text-3xl font-bold text-slate-900 mb-6">Privacy Policy</h1>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8 text-amber-800 text-sm">
                <strong>Note:</strong> Treno Web is a portfolio demonstration project. It is not affiliated with Indian Railways or IRCTC.
            </div>

            <section className="space-y-6 text-slate-700">
                <div>
                    <h2 className="text-xl font-semibold text-slate-900 mb-2">1. Overview</h2>
                    <p>
                        This application is built solely for educational and demonstration purposes.
                        It simulates a train search experience but does not process real bookings or payments.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-slate-900 mb-2">2. Data Collection</h2>
                    <p>
                        We do not collect any personal data. Search queries (station codes, dates) are processed locally
                        or sent to our demo backend to retrieve schedule information, but are not stored permanently
                        or linked to user identities.
                    </p>
                    <ul className="list-disc pl-5 mt-2 space-y-1">
                        <li>No cookies are used for tracking.</li>
                        <li>No user accounts are required.</li>
                        <li>No PNR or booking details are processed.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-slate-900 mb-2">3. Disclaimer</h2>
                    <p>
                        Please do not enter any real sensitive personal information (PII) into this application.
                        The train schedule data presented may be outdated or simulated and should not be relied upon for actual travel.
                    </p>
                </div>

                <div className="pt-6 border-t border-slate-200 mt-8">
                    <p className="text-sm text-slate-500">
                        Last updated: February 2026
                    </p>
                </div>
            </section>
        </main>
    );
}
