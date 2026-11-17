# System prompt comparison

- **Provider:** gemini
- **Model:** gemini-3.5-flash-lite
- **Run time:** 2026-11-17T20:59:57+05:00
- **Same user request:** Explain BFS and DFS to a beginner, then give one practical use case for each.

## A — Basic

**System prompt:** You are a helpful assistant. Answer the user's question clearly.

**Model response:**

Imagine you are trying to find a book in a massive, multi-room library. How would you search through it? **BFS** and **DFS** are two different strategies (or "algorithms") for searching through data that is connected like a web or a family tree (technically called a **graph** or **tree**).

Here is how they work in plain English.

---

### 1. BFS (Breadth-First Search)
* **The Strategy:** **Go wide before you go deep.**
* **The Library Analogy:** You start at the front door. You look at every book on the first shelf of Room 1. Then you look at every book on the second shelf. Then you move to Room 2 and look at all its shelves. You explore level by level, staying close to the start before venturing far away.
* **How it works technically:** It uses a "Queue" (like a line at a grocery store—first in, first out). It checks all the immediate neighbors of a starting point, then checks all *their* neighbors, moving outward in expanding ripples.

**Practical Use Case for BFS: Finding the shortest path on a map.**
If you use Google Maps to find the quickest route from your house to a coffee shop, it uses BFS. It fans out equally in all directions from your starting point until it hits the destination. Because it explores equally in all directions, the first time it reaches your destination, it is guaranteed to be the shortest route.

---

### 2. DFS (Depth-First Search)
* **The Strategy:** **Go deep before you go wide.**
* **The Library Analogy:** You walk into the library, pick the very first aisle, walk all the way to the back, pick the very first shelf, pull out the first book, and keep going down that single path until you hit a dead end. Only then do you back up to the last junction and try a different path.
* **How it works technically:** It uses a "Stack" (like a pile of plates—last in, first out). It dives down a path as far as possible until it can't go any further, then backtracks.

**Practical Use Case for DFS: Solving a maze.**
If you are dropped inside a physical maze, a natural human instinct is DFS. You walk down a corridor until you hit a dead end, turn around, go back to the last fork in the road, and try a different path. DFS is fantastic for exploring *every* possibility until it finds a solution or exits the maze.

---

### Summary: Which is better?
* Use **BFS** if you want the **shortest/quickest** path to something.
* Use **DFS** if you want to **explore every possible corner** or path, or if the answer is likely hidden very deep down a single track.

## B — Role + constraints

**System prompt:** You are a patient computer science tutor. Explain concepts for a first-year student. Use simple language, one concise definition per concept, and one practical use case each. Do not add unrelated details.

**Model response:**

**BFS (Breadth-First Search)** is a graph traversal algorithm that explores neighbor nodes level by level before moving deeper.
* **Practical Use Case:** Finding the shortest path between two people on a social media network.

**DFS (Depth-First Search)** is a graph traversal algorithm that explores as deep as possible down one path before backtracking.
* **Practical Use Case:** Solving a maze by following one path until you hit a dead end, then turning back.

## C — Role + structure + example

**System prompt:** You are an exam-focused computer science tutor. Explain BFS and DFS in simple language. For each: give the core idea, a small real-world analogy, and one practical use case. Finish with a compact comparison table. Example style: 'BFS checks nearby nodes before moving deeper.' Be accurate and avoid unsupported claims.

**Model response:**

Here is a clear, exam-focused breakdown of Breadth-First Search (BFS) and Depth-First Search (DFS).

---

### **1. Breadth-First Search (BFS)**
* **Core Idea:** BFS explores a graph level by level. It checks all immediate neighbors of a node before moving one level deeper. It uses a **Queue** (First-In, First-Out / FIFO).
* **Real-world Analogy:** Ripples in a pond. When you drop a stone, the water ripples outward in expanding concentric circles, touching closer points before points further away.
* **Practical Use Case:** **Shortest path in unweighted graphs.** For example, finding the quickest route on a social network (like "Degrees of Separation" on LinkedIn) to connect you to a user 2 connections away rather than 10.

---

### **2. Depth-First Search (DFS)**
* **Core Idea:** DFS dives as deep as possible down a single path before backing up (backtracking) to try other paths. It uses a **Stack** (Last-In, First-Out / LIFO) or recursion.
* **Real-world Analogy:** Solving a physical maze. You pick a path and walk until you hit a dead end, then retrace your steps to the last junction and try a different path.
* **Practical Use Case:** **Pathfinding and cycle detection.** For example, solving maze puzzles or checking if a graph contains a loop (cycle detection in dependency graphs).

---

### **Quick Comparison Table**

| Feature | BFS (Breadth-First Search) | DFS (Depth-First Search) |
| :--- | :--- | :--- |
| **Strategy** | Broad (level by level) | Deep (path by path) |
| **Data Structure** | Queue (FIFO) | Stack (LIFO) or Recursion |
| **Shortest Path?** | Yes (guaranteed for unweighted) | No |
| **Memory Usage** | Higher (stores wide levels) | Lower (stores single paths) |

## Comparison — observed differences

| Version | What improved? | What was missing? |
|---|---|---|
| A — Basic | Detailed explanations and relatable analogies made BFS and DFS easy to visualize. | The answer was overly lengthy and made an inaccurate generalization about Google Maps using BFS. |
| B — Role + constraints | Definitions were concise, direct, and easy to revise. | It lacked detailed analogies, data structures, and a comparison table. |
| C — Role + structure + example | The structured format included core ideas, analogies, Queue and Stack, use cases, and a comparison table. | It was longer than Prompt B, although more comprehensive for exam preparation. |

**Accuracy note:** The Google Maps example in version A is overgeneralized: standard BFS guarantees shortest paths in unweighted graphs; road navigation generally involves weighted routing, so the response's claim should not be treated as a factual description of Google Maps.
