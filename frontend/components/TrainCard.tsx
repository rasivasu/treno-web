import { ClockIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

interface TrainCardProps {
  trainNumber: string;
  trainName: string;
  fromStation: string;
  toStation: string;
  departureTime: string;
  arrivalTime: string;
  duration: string;
}

export default function TrainCard({
  trainNumber,
  trainName,
  fromStation,
  toStation,
  departureTime,
  arrivalTime,
  duration,
}: TrainCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{trainName || 'N/A'}</h3>
          <p className="text-sm text-slate-500 font-mono">#{trainNumber || 'N/A'}</p>
        </div>
        <div className="text-right">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Available
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between text-slate-700">
        <div className="flex flex-col">
          <span className="text-2xl font-bold">{departureTime}</span>
          <span className="text-xs text-slate-500">{fromStation}</span>
        </div>

        <div className="flex flex-col items-center px-4 flex-1">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
            <ClockIcon className="h-3 w-3" />
            {duration}
          </div>
          <div className="w-full h-px bg-slate-200 relative flex items-center justify-center">
            <ArrowRightIcon className="h-4 w-4 text-slate-400 bg-white px-1 absolute" />
          </div>
        </div>

        <div className="flex flex-col text-right">
          <span className="text-2xl font-bold">{arrivalTime}</span>
          <span className="text-xs text-slate-500">{toStation}</span>
        </div>
      </div>
    </div>
  );
}
