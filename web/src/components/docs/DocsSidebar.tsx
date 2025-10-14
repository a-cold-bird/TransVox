'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, ChevronDown, Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Icon } from '@/components/ui/icon'
import { docsNavigation } from '@/data/docs/navigation'
import { useTranslation } from '@/hooks/useTranslation'
import type { DocNavItem } from '@/types/docs'

export function DocsSidebar() {
  const pathname = usePathname()
  const { t } = useTranslation()
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(docsNavigation.map((section) => section.title))
  )

  const toggleSection = (sectionTitle: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionTitle)) {
      newExpanded.delete(sectionTitle)
    } else {
      newExpanded.add(sectionTitle)
    }
    setExpandedSections(newExpanded)
  }

  const isActive = (href: string) => {
    return pathname === href
  }

  const NavItem = ({ item, level = 0 }: { item: DocNavItem; level?: number }) => {
    const hasChildren = item.items && item.items.length > 0
    const isExpanded = expandedSections.has(item.title)
    const active = item.href ? isActive(item.href) : false

    return (
      <div className="space-y-1">
        {item.href ? (
          <Link
            href={item.href}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
              'hover:bg-muted/50',
              active
                ? 'bg-muted text-foreground font-medium'
                : 'text-muted-foreground hover:text-foreground',
              level > 0 && 'ml-4'
            )}
            onClick={() => setIsMobileOpen(false)}
          >
            {item.icon && <Icon icon={item.icon} className="h-4 w-4" />}
            <span className="flex-1">{t(item.title)}</span>
            {item.badge && (
              <span className="px-1.5 py-0.5 text-xs rounded bg-primary/20 text-primary">
                {item.badge}
              </span>
            )}
          </Link>
        ) : (
          <button
            onClick={() => toggleSection(item.title)}
            className={cn(
              'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
              'hover:bg-muted/50 text-foreground',
              level > 0 && 'ml-4'
            )}
          >
            {hasChildren &&
              (isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              ))}
            {item.icon && <Icon icon={item.icon} className="h-4 w-4" />}
            <span className="flex-1 text-left font-medium">{t(item.title)}</span>
          </button>
        )}

        {hasChildren && isExpanded && (
          <div className="space-y-1">
            {item.items!.map((child, idx) => (
              <NavItem key={idx} item={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    )
  }

  const SidebarContent = () => (
    <div className="space-y-6 py-6">
      {docsNavigation.map((section, idx) => {
        const isExpanded = expandedSections.has(section.title)
        return (
          <div key={idx} className="space-y-2">
            <button
              onClick={() => toggleSection(section.title)}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              {t(section.title)}
            </button>
            {isExpanded && (
              <div className="space-y-1">
                {section.items.map((item, itemIdx) => (
                  <NavItem key={itemIdx} item={item} />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed bottom-4 right-4 z-50 p-3 rounded-full bg-background border border-border shadow-lg hover:bg-muted transition-colors"
        aria-label="Toggle navigation"
      >
        {isMobileOpen ? (
          <X className="h-5 w-5 text-foreground" />
        ) : (
          <Menu className="h-5 w-5 text-foreground" />
        )}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64',
          'bg-background border-r border-border',
          'overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent',
          'transition-transform duration-300',
          'lg:translate-x-0',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <SidebarContent />
      </aside>

      {/* Sidebar Spacer for Desktop */}
      <div className="hidden lg:block w-64 flex-shrink-0" />
    </>
  )
}
