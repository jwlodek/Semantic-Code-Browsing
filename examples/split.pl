reverse(L,R) :- reverse_helper(L, [], R).
reverse_helper([H|T], Acc, R) :- reverse_helper(T, [H|Acc], R).
reverse_helper([], Acc, Acc).
split([], [], []).
split(L, X, Y) :- split_helper(L, Odd, Even, 0, [], []), reverse(Odd, X), reverse(Even, Y).
split_helper([], Odd, Even, _, Odd, Even).
split_helper([H|T], X, Y, 0, Odd, Even) :- split_helper(T, X, Y, 1, [H|Odd], Even).
split_helper([H|T], X, Y, 1, Odd, Even) :- split_helper(T, X, Y, 0, Odd, [H|Even]).