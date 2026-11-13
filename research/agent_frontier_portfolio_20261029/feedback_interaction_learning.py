"""Candidate generative-policy update from native feedback/repair interactions.

The row objective is established relative-reward regression (e.g. REBEL).
The cross-context term is centered least squares, not a new statistical theorem.
The research hypothesis concerns execution-derived interaction supervision;
task benefits over matched row regression/DPO remain unverified.

Inputs score two complete corrective fragments in two public contexts. Each
fragment's score sums only its actual assistant/tool-call token log probabilities.
Native utilities must cover that same fragment plus the declared continuation.
No first-action success labels, generated diagnoses, or hidden state are used.
"""
import math


def interaction_update(policy_logp, reference_logp, utilities, observed, *,
                       behavior_clone, beta=1., row_weight=1.,
                       interaction_weight=1., contrast_floor=0.):
    """Return differentiable losses for [batch, 2 contexts, 2 fragments].

    beta is the declared KL regularization scale, not an arbitrary division of
    success counts. A regularized policy-improvement target has relative reward
    beta * (log pi - log reference). Interactions cancel shared action offsets;
    row anchors remain necessary because a sum constraint cannot identify rows.

    Missing native cells must be NaN with observed=False. Known equal outcomes
    receive no preference loss. They remain in the source data and BC replay.
    This masks unsupported comparisons; it does not prove system equality.
    """
    import torch
    values = (beta, row_weight, interaction_weight, contrast_floor)
    if (not all(math.isfinite(x) for x in values) or beta <= 0
            or min(row_weight, interaction_weight, contrast_floor) < 0):
        raise ValueError('invalid objective scales')
    if (policy_logp.ndim != 3 or policy_logp.shape[-2:] != (2, 2)
            or policy_logp.shape != reference_logp.shape
            or policy_logp.shape != utilities.shape
            or policy_logp.shape != observed.shape or observed.dtype != torch.bool):
        raise ValueError('aligned [batch, 2, 2] scores, utilities and bool mask required')
    if not policy_logp.is_floating_point() or policy_logp.shape[0] == 0:
        raise ValueError('nonempty floating-point policy scores required')
    if (not torch.isfinite(policy_logp).all()
            or not torch.isfinite(reference_logp).all()
            or not torch.isfinite(utilities[observed]).all()
            or not torch.isnan(utilities[~observed]).all()):
        raise ValueError('finite known values and explicit NaN for unknown utilities required')
    if len({x.device for x in (policy_logp, reference_logp, utilities, observed)}) != 1:
        raise ValueError('all objective inputs must share a device')
    clone = torch.as_tensor(behavior_clone, dtype=policy_logp.dtype, device=policy_logp.device)
    if clone.ndim != 0 or not torch.isfinite(clone):
        raise ValueError('finite scalar BC loss required')
    # Reference policy and native execution outcomes supply fixed supervision.
    reward = torch.where(observed, utilities.detach(), torch.zeros_like(utilities))
    delta = policy_logp - reference_logp.detach()
    model_difference = beta * (delta[..., 0] - delta[..., 1])
    native_difference = reward[..., 0] - reward[..., 1]
    eligible_rows = observed.all(dim=-1) & (native_difference.abs() > contrast_floor)
    error = model_difference - native_difference
    row_loss = (error.square() * eligible_rows).sum() / eligible_rows.sum().clamp_min(1)
    eligible_pairs = eligible_rows.all(dim=-1)
    pair_error = error[:, 0] - error[:, 1]
    interaction_loss = (pair_error.square() * eligible_pairs).sum() / eligible_pairs.sum().clamp_min(1)
    total = clone + row_weight * row_loss + interaction_weight * interaction_loss
    return dict(total=total, behavior_clone=clone, row=row_loss,
                interaction=interaction_loss,
                eligible_rows=int(eligible_rows.sum().detach()),
                eligible_pairs=int(eligible_pairs.sum().detach()),
                native_difference=native_difference.detach())
