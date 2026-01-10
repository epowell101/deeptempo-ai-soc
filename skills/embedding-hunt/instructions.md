# Embedding Hunt - Detailed Instructions

## Understanding Embedding Similarity

### What Does Similarity Mean?

When two findings have high embedding similarity, it means the LogLM detected similar behavioral patterns. This could indicate:

- Same attack technique
- Same tool or malware family
- Same actor's TTPs
- Similar legitimate behavior

### Similarity Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| >0.95 | Near-identical behavior | Likely same activity/actor |
| 0.90-0.95 | Very similar | Strong relationship |
| 0.80-0.90 | Related pattern | Worth investigating |
| 0.70-0.80 | Loosely related | May be coincidental |
| <0.70 | Different behavior | Probably unrelated |

## Hunt Strategies

### Strategy 1: Scope Assessment

**Goal**: Determine how widespread a behavior is

```
1. Start with seed finding
2. Get k=100 neighbors
3. Count unique entities
4. Assess: Isolated vs. Widespread
```

### Strategy 2: Timeline Reconstruction

**Goal**: Build a chronological view of activity

```
1. Get neighbors within time window
2. Sort by timestamp
3. Identify first and last occurrence
4. Look for patterns (bursts, regularity)
```

### Strategy 3: Entity Pivot

**Goal**: Find all suspicious activity for an entity

```
1. Get neighbors for seed
2. Filter to specific entity
3. Analyze all behaviors for that entity
4. Build entity risk profile
```

### Strategy 4: Technique Hunting

**Goal**: Find all instances of a specific technique

```
1. Get neighbors for seed
2. Filter by MITRE technique
3. Analyze technique variations
4. Identify detection gaps
```

## Analyzing Results

### Identifying Natural Clusters

Look for:
- **Similarity gaps**: Sharp drops in similarity indicate cluster boundaries
- **Entity groupings**: Findings naturally group by entity
- **Temporal groupings**: Activity clusters in time
- **Technique groupings**: Consistent MITRE predictions

### Red Flags in Hunt Results

- Multiple entities with near-identical behavior
- Activity spanning unusual time periods
- Consistent external destinations
- Technique progressions (recon → access → exfil)

### False Positive Indicators

- Known legitimate applications
- Regular business processes
- Scheduled tasks
- Backup/sync operations

## Documentation Best Practices

### Hunt Hypothesis

Always document:
```
Hypothesis: [What you expect to find]
Seed: [Finding ID and why chosen]
Scope: [Time range, entity scope]
Success Criteria: [What would confirm/refute hypothesis]
```

### Hunt Log

Track your steps:
```
1. [Timestamp] Initial query: k=10, [results summary]
2. [Timestamp] Expanded: k=50, [observations]
3. [Timestamp] Applied filter: [filter], [impact]
4. [Timestamp] Identified cluster: [description]
```

### Findings Documentation

For each significant finding:
```
Finding: [ID]
Similarity: [score]
Relevance: [why it matters]
Action: [what to do with it]
```
