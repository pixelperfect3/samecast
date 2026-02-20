# Game Ideas: Six Degrees of Separation

Inspired by "Six Degrees of Kevin Bacon" — a daily puzzle game built on top of SameCast's TMDB data.

## 1. CastChain (closest to Six Degrees)

Given two actors, find the shortest chain of movies connecting them. Each step must be a movie where two actors both appeared.

- **Wordle twist**: Daily puzzle with a target chain length (par). Score based on how few steps you take.
- **Hints**: Reveal one movie in the chain, or show the genre of the connecting film.
- **Example**: Tom Hanks → *The Terminal* → Catherine Zeta-Jones → *Ocean's Twelve* → Brad Pitt

## 2. SameCast Daily

Given two movies, guess which actors/crew they share — one guess at a time.

- **Wordle twist**: 6 guesses to name all shared cast. After each guess, told if that person is in both, just one, or neither.
- **Scoring**: Stars for getting the top-billed shared actors first.
- **Example**: "The Dark Knight & Inception" — guess "Cillian Murphy" ✅, guess "Leonardo DiCaprio" ❌ (only in Inception)

## 3. WhoAmI?

Daily puzzle: given clues about a mystery actor based on their filmography, guess who they are.

- **Round 1**: "Appeared in a 2008 superhero film and a 2010 sci-fi film" (vague)
- **Round 2**: "Shared a cast with Liam Neeson in both"
- **Round 3**: Reveal one movie title
- **Wordle twist**: Fewer clues needed = better score. Share your score like 🟩🟩⬛⬛⬛⬛

## 4. OddOneOut

Show 4 actors — 3 appeared in the same movie, 1 didn't. Guess the odd one out.

- **Wordle twist**: 5 rounds daily, increasing difficulty. Easy = blockbusters, Hard = indie films.
- **Shareable**: "OddOneOut #142: 5/5 🟩🟩🟩🟨🟩"

## 5. FilmLink

Daily challenge: connect Actor A to Actor B in exactly N steps, where each step is naming a movie. The catch — you can only use movies from a specific constraint (decade, genre, language).

- **Example**: Connect Bryan Cranston to Jessica Walter in 3 steps, using only TV shows.
- **Wordle twist**: One puzzle per day, everyone gets the same pair. Share your path.

## Feasibility

| Game | New data needed | Complexity |
|------|----------------|------------|
| **CastChain** | Graph traversal (BFS across credits) | Medium-high |
| **SameCast Daily** | Almost nothing — pick two titles daily | **Low** |
| **WhoAmI?** | Clue generation logic | Medium |
| **OddOneOut** | Random sampling from shared casts | Low-medium |
| **FilmLink** | Same as CastChain but constrained | Medium-high |

**SameCast Daily** is the quickest to ship — the comparison engine already exists. Just needs a daily puzzle picker, guess input, and scoring/share system.
