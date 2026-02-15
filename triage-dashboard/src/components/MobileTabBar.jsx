import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard, HeartPulse, Wind, Crosshair, ClipboardList, Settings
} from 'lucide-react';

const tabs = [
    { to: '/', icon: LayoutDashboard, label: 'Home' },
    { to: '/heart-exam', icon: HeartPulse, label: 'Heart' },
    { to: '/lung-exam', icon: Wind, label: 'Lung' },
    { to: '/placement-guide', icon: Crosshair, label: 'Guide' },
    { to: '/results', icon: ClipboardList, label: 'Results' },
    { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function MobileTabBar() {
    return (
        <nav className="mobile-tab-bar">
            {tabs.map(tab => (
                <NavLink
                    key={tab.to}
                    to={tab.to}
                    className={({ isActive }) =>
                        `mobile-tab ${isActive ? 'active' : ''}`
                    }
                    end={tab.to === '/'}
                >
                    <tab.icon size={20} />
                    <span>{tab.label}</span>
                </NavLink>
            ))}
        </nav>
    );
}
