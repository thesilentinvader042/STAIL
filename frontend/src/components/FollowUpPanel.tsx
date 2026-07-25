import { useState } from 'react';

export interface FollowUpTask {
  id: string;
  title: string;
  due_date: string;
  priority: 'Urgent' | 'High' | 'Normal';
  notes?: string;
  completed: boolean;
}

interface Props {
  leadId?: string;
  leadName?: string;
}

export default function FollowUpPanel({ leadId, leadName }: Props) {
  const [tasks, setTasks] = useState<FollowUpTask[]>([
    {
      id: 'task-1',
      title: 'Call prospect to confirm budget and location preferences',
      due_date: new Date(Date.now() + 86400000).toISOString(),
      priority: 'High',
      notes: 'Ensure they have pre-approved home loan details ready.',
      completed: false,
    },
    {
      id: 'task-2',
      title: 'Send top 3 shortlisted 3BHK listings PDF catalog',
      due_date: new Date(Date.now() + 172800000).toISOString(),
      priority: 'Normal',
      completed: false,
    },
  ]);

  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDueDate, setNewDueDate] = useState('');
  const [newPriority, setNewPriority] = useState<'Urgent' | 'High' | 'Normal'>('Normal');
  const [newNotes, setNewNotes] = useState('');

  const handleToggleComplete = (taskId: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, completed: !t.completed } : t))
    );
  };

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const newTask: FollowUpTask = {
      id: `task-${Date.now()}`,
      title: newTitle.trim(),
      due_date: newDueDate || new Date(Date.now() + 86400000).toISOString(),
      priority: newPriority,
      notes: newNotes.trim() || undefined,
      completed: false,
    };

    setTasks([newTask, ...tasks]);
    setNewTitle('');
    setNewDueDate('');
    setNewPriority('Normal');
    setNewNotes('');
    setShowModal(false);
  };

  const getPriorityBadge = (p: FollowUpTask['priority']) => {
    switch (p) {
      case 'Urgent':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'High':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4 text-slate-100">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Follow-Up Reminders
          </h3>
          <p className="text-[11px] text-slate-400">
            Task reminders for {leadName || 'this prospect'}
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="rounded-xl bg-blue-600 hover:bg-blue-500 px-3 py-1.5 text-xs font-bold text-white transition-colors flex items-center gap-1 shadow-md shadow-blue-500/20"
        >
          <span>+</span> Add Task
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No follow-up tasks scheduled. Click "+ Add Task" to create one.
        </div>
      ) : (
        <div className="space-y-2.5">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`flex items-start justify-between gap-3 rounded-xl border p-3.5 transition-all ${
                task.completed
                  ? 'border-slate-800/60 bg-slate-950/40 opacity-60'
                  : 'border-slate-800 bg-slate-950/80 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={() => handleToggleComplete(task.id)}
                  className="mt-0.5 h-4 w-4 rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0 cursor-pointer"
                />

                <div className="space-y-1 flex-1 min-w-0">
                  <p
                    className={`text-xs font-medium text-slate-200 leading-snug ${
                      task.completed ? 'line-through text-slate-400' : ''
                    }`}
                  >
                    {task.title}
                  </p>
                  {task.notes && (
                    <p className="text-[11px] text-slate-400 truncate">{task.notes}</p>
                  )}
                  <p className="text-[10px] text-slate-500">
                    Due:{' '}
                    {new Date(task.due_date).toLocaleString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>

              <span
                className={`rounded-md px-2 py-0.5 text-[10px] font-bold border shrink-0 ${getPriorityBadge(
                  task.priority
                )}`}
              >
                {task.priority}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Add Task Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-2xl space-y-4 text-slate-100">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h4 className="font-bold text-sm text-white">Create Follow-Up Task</h4>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-300">Task Description</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Follow up regarding site visit timing..."
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-300">Due Date & Time</label>
                  <input
                    type="datetime-local"
                    value={newDueDate}
                    onChange={(e) => setNewDueDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2 text-xs text-slate-100 focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-300">Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as any)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2 text-xs text-slate-100 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="Normal">Normal</option>
                    <option value="High">High</option>
                    <option value="Urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-300">Notes (Optional)</label>
                <textarea
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  placeholder="Add extra details or reminders..."
                  className="w-full h-20 rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-500 shadow-md shadow-blue-500/20"
                >
                  Save Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
