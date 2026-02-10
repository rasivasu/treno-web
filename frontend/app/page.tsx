import SearchWidget from '../components/SearchWidget';

export default function Home() {
    return (
        <main className="flex flex-col items-center justify-center p-4 py-20">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
                        Find your train
                    </h1>
                    <p className="mt-4 text-lg text-slate-600">
                        Instant search for local and express trains.
                    </p>
                </div>

                <SearchWidget />
            </div>
        </main>
    );
}
