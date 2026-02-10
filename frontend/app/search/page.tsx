'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import TrainCard from '../../components/TrainCard';

interface TrainResult {
    train_number: string;
    train_name: string;
    from_station_name: string;
    to_station_name: string;
    departure_time: string;
    arrival_time: string;
    duration: string;
}

function SearchContent() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const fromCode = searchParams.get('from');
    const toCode = searchParams.get('to');
    const date = searchParams.get('date');

    const [results, setResults] = useState<TrainResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!fromCode || !toCode || !date) {
            setLoading(false);
            return;
        }

        const fetchTrains = async () => {
            setLoading(true);
            setError('');
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiUrl}/api/search?from_station=${fromCode}&to_station=${toCode}&date=${date}`);
                if (!res.ok) {
                    throw new Error('Failed to fetch trains');
                }
                const data = await res.json();
                setResults(data.results || []);
            } catch (err) {
                console.error(err);
                setError('Failed to load train results. Please try again.');
                toast.error("Could not connect to server. Please check your connection.");
            } finally {
                setLoading(false);
            }
        };

        fetchTrains();
    }, [fromCode, toCode, date]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                    <p className="text-slate-500">Finding best trains for you...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <button
                    onClick={() => router.push('/')}
                    className="text-sm text-slate-500 hover:text-slate-700 underline flex items-center gap-1"
                >
                    ← Back to search
                </button>
            </div>

            <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-4 bg-white/50 backdrop-blur-sm rounded-2xl px-6 border border-slate-200">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                        {fromCode} <span className="text-slate-400 text-sm">→</span> {toCode}
                    </h2>
                    <p className="text-sm text-slate-500 mt-1">
                        {date} • {results.length} Trains found
                    </p>
                </div>
                <button
                    onClick={() => router.push('/')}
                    className="text-sm font-medium text-indigo-600 bg-indigo-50 px-4 py-2 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                    Modify Search
                </button>
            </header>

            {error ? (
                <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-100 text-center">
                    {error}
                </div>
            ) : results.length === 0 ? (
                <div className="text-center py-12">
                    <p className="text-slate-500 text-lg">No direct trains found between these stations.</p>
                    <button onClick={() => router.push('/')} className="mt-4 text-indigo-600 hover:underline">Try another search</button>
                </div>
            ) : (
                <div className="space-y-4">
                    {results.map((train) => (
                        <TrainCard
                            key={train.train_number}
                            trainNumber={train.train_number}
                            trainName={train.train_name}
                            fromStation={train.from_station_name}
                            toStation={train.to_station_name}
                            departureTime={train.departure_time}
                            arrivalTime={train.arrival_time}
                            duration={train.duration}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default function SearchResults() {
    return (
        <main className="p-4">
            <Suspense fallback={<div className="text-center py-20">Loading search...</div>}>
                <SearchContent />
            </Suspense>
        </main>
    );
}
