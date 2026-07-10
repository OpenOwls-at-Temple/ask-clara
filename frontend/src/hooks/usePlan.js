import { useState } from "react";
import { generatePlan, getPlan, updatePlanItem } from "../services/plan";

export function usePlan() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const data = await getPlan();
      setPlan(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const result = await generatePlan();
      setPlan(result);
      return result;
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function toggleItem(index) {
    if (!plan) return;
    const next =
      plan.items[index].status === "complete" ? "pending" : "complete";
    setError(null);
    try {
      const updated = await updatePlanItem(plan.id, index, next);
      setPlan(updated);
    } catch (err) {
      setError(err);
    }
  }

  return { plan, loading, error, load, generate, toggleItem };
}
