"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

interface Category {
  id: number
  name: string
}

const Onboarding = () => {
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategories, setSelectedCategories] = useState<number[]>([])
  const router = useRouter()

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api/categories")
        if (!response.ok) {
          throw new Error("Failed to fetch categories")
        }
        const data = await response.json()
        setCategories(data)
      } catch (error) {
        console.error("Error fetching categories:", error)
        toast.error("카테고리 조회 실패", {
          description: "카테고리 정보를 불러오지 못했습니다. 다시 시도해주세요.",
        })
      }
    }

    fetchCategories()
  }, [])

  const toggleCategory = (categoryId: number) => {
    setSelectedCategories((prevSelected) => {
      if (prevSelected.includes(categoryId)) {
        return prevSelected.filter((id) => id !== categoryId)
      } else {
        return [...prevSelected, categoryId]
      }
    })
  }

  const handleSubmit = async () => {
    if (selectedCategories.length === 0) {
      toast.error("카테고리 선택 필요", {
        description: "1개 이상의 카테고리를 선택해주세요.",
      })
      return
    }

    try {
      const response = await fetch("/api/user/update-categories", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ categories: selectedCategories }),
      })

      if (!response.ok) {
        throw new Error("Failed to update user categories")
      }

      router.push("/dashboard")
    } catch (error) {
      console.error("Error updating user categories:", error)
      toast.error("서버 저장 실패", {
        description: "서버 저장에 실패했습니다. 다시 시도해주세요.",
      })
    }
  }

  return (
    <div>
      <h1>Welcome! Please select your interests:</h1>
      <div>
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => toggleCategory(category.id)}
            style={{
              backgroundColor: selectedCategories.includes(category.id) ? "lightblue" : "white",
              margin: "5px",
              padding: "5px 10px",
              border: "1px solid gray",
              borderRadius: "5px",
            }}
          >
            {category.name}
          </button>
        ))}
      </div>
      <button onClick={handleSubmit}>Save & Continue</button>
    </div>
  )
}

export default Onboarding
