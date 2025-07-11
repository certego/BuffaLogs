import * as React from "react";
import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// Mock subject data
const SUBJECTS = [
  {
    name: "Chemistry",
    interested: 57,
    teacher: true,
    courses: 4,
    level: "Intermediate",
  },
  {
    name: "Mathematics",
    interested: 82,
    teacher: true,
    courses: 7,
    level: "Advanced",
  },
  {
    name: "Programming",
    interested: 134,
    teacher: false,
    courses: 3,
    level: "Beginner",
  },
  {
    name: "Psychology",
    interested: 29,
    teacher: true,
    courses: 1,
    level: "Beginner",
  },
  {
    name: "Electronics",
    interested: 16,
    teacher: false,
    courses: 0,
    level: "Intermediate",
  },
  {
    name: "Geography",
    interested: 48,
    teacher: true,
    courses: 2,
    level: "Beginner",
  },
  {
    name: "Literature",
    interested: 65,
    teacher: true,
    courses: 3,
    level: "Intermediate",
  },
  {
    name: "Music Theory",
    interested: 22,
    teacher: true,
    courses: 2,
    level: "Beginner",
  },
  {
    name: "Robotics",
    interested: 73,
    teacher: false,
    courses: 5,
    level: "Advanced",
  },
  {
    name: "Health & Wellness",
    interested: 41,
    teacher: true,
    courses: 2,
    level: "Beginner",
  },
];

const LEVELS = ["All Levels", "Beginner", "Intermediate", "Advanced"];
const SORT_OPTIONS = ["Newest", "A-Z", "Z-A"];

export default function SubjectsPage() {
  const [search, setSearch] = useState("");
  const [minInterested, setMinInterested] = useState(0);
  const [level, setLevel] = useState("All Levels");
  const [minCourses, setMinCourses] = useState(0);
  const [teacher, setTeacher] = useState("any");
  const [sort, setSort] = useState("Newest");

  const filteredSubjects = useMemo(() => {
    let filtered = SUBJECTS.filter((s) =>
      s.name.toLowerCase().includes(search.toLowerCase())
    );
    if (minInterested > 0) filtered = filtered.filter((s) => s.interested >= minInterested);
    if (level !== "All Levels") filtered = filtered.filter((s) => s.level === level);
    if (minCourses > 0) filtered = filtered.filter((s) => s.courses >= minCourses);
    if (teacher !== "any") filtered = filtered.filter((s) => s.teacher === (teacher === "yes"));
    if (sort === "A-Z") filtered = filtered.sort((a, b) => a.name.localeCompare(b.name));
    if (sort === "Z-A") filtered = filtered.sort((a, b) => b.name.localeCompare(a.name));
    return filtered;
  }, [search, minInterested, level, minCourses, teacher, sort]);

  return (
    <div className="flex flex-row min-h-screen bg-background">
      {/* Filter Sidebar */}
      <aside className="w-80 p-6 border-r border-border bg-card">
        <h2 className="text-xl font-bold mb-4">Filters</h2>
        <div className="mb-4">
          <label className="block mb-1">Search</label>
          <Input
            placeholder="Search subjects..."
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1">Number of interested students</label>
          <select
            className="w-full border rounded p-2"
            value={minInterested}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMinInterested(Number(e.target.value))}
          >
            <option value={0}>All</option>
            <option value={50}>50+</option>
            <option value={100}>100+</option>
          </select>
        </div>
        <div className="mb-4">
          <label className="block mb-1">Level</label>
          <select
            className="w-full border rounded p-2"
            value={level}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setLevel(e.target.value)}
          >
            {LEVELS.map((lvl) => (
              <option key={lvl} value={lvl}>{lvl}</option>
            ))}
          </select>
        </div>
        <div className="mb-4">
          <label className="block mb-1">Number of courses</label>
          <input
            type="number"
            min={0}
            className="w-full border rounded p-2"
            value={minCourses}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMinCourses(Number(e.target.value))}
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1">Available teacher</label>
          <select
            className="w-full border rounded p-2"
            value={teacher}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setTeacher(e.target.value)}
          >
            <option value="any">Any</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <div className="mb-4">
          <label className="block mb-1">Sort By</label>
          <select
            className="w-full border rounded p-2"
            value={sort}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSort(e.target.value)}
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>
      </aside>
      {/* Subjects Grid */}
      <main className="flex-1 p-10">
        <h1 className="text-3xl font-bold mb-8">Explore Subjects</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredSubjects.map((subject) => (
            <div key={subject.name} className="border rounded-lg p-6 bg-card shadow">
              <h2 className="text-xl font-semibold mb-2">{subject.name}</h2>
              <p className="mb-1"><b>Interested:</b> {subject.interested} learners</p>
              <p className="mb-1"><b>Teacher Available:</b> {subject.teacher ? "Yes" : "No"}</p>
              <p className="mb-1"><b>Courses:</b> {subject.courses}</p>
              <p className="mb-4"><b>Level:</b> {subject.level}</p>
              <div className="flex gap-2">
                <Button variant="secondary">Teach</Button>
                <Button variant="default">Learn</Button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
} 