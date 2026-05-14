import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../providers/volunteer_provider.dart';
import '../../widgets/match_result_card.dart';

class MatchScreen extends StatefulWidget {
  const MatchScreen({super.key});

  @override
  State<MatchScreen> createState() => _MatchScreenState();
}

class _MatchScreenState extends State<MatchScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Text(
          'Intelligence Hub',
          style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w900, letterSpacing: -1),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome_rounded, color: Color(0xFF00BFA5)),
            onPressed: () => _showMatchingExplanation(context),
            tooltip: 'How AI Matching Works',
          ),
        ],
      ),
      body: Consumer<VolunteerProvider>(
        builder: (context, provider, child) {
          if (provider.isMatchingInProgress) {
            return _buildLoadingState(provider);
          }

          if (provider.matchResults.isEmpty) {
            return _buildEmptyState(provider);
          }

          return _buildResultsList(provider);
        },
      ),
    );
  }

  Widget _buildLoadingState(VolunteerProvider provider) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(color: Color(0xFF00BFA5), strokeWidth: 3),
          const SizedBox(height: 32),
          Text(
            'GEMINI IS ANALYZING...',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF00BFA5),
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Optimizing field deployment for\n${provider.volunteers.length} active responders',
            textAlign: TextAlign.center,
            style: GoogleFonts.plusJakartaSans(
              color: const Color(0xFF64748B),
              fontSize: 14,
              fontWeight: FontWeight.w600,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(VolunteerProvider provider) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        children: [
          const SizedBox(height: 60),
          Container(
            padding: const EdgeInsets.all(40),
            decoration: BoxDecoration(
              color: const Color(0xFF00BFA5).withOpacity(0.05),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.psychology_rounded, size: 100, color: Color(0xFF00BFA5)),
          ),
          const SizedBox(height: 40),
          Text(
            'Smart Intelligence',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 28,
              fontWeight: FontWeight.w900,
              color: const Color(0xFF0F172A),
              letterSpacing: -1,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Match available responders to the most critical community missions using Gemini-powered logic.',
            textAlign: TextAlign.center,
            style: GoogleFonts.plusJakartaSans(
              color: const Color(0xFF64748B),
              fontSize: 15,
              fontWeight: FontWeight.w500,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 48),
          ElevatedButton(
            onPressed: () => provider.runMatching(),
            child: const Text('RUN AI ANALYSIS'),
          ),
          const SizedBox(height: 24),
          TextButton.icon(
            onPressed: () => _showMatchingExplanation(context),
            icon: const Icon(Icons.info_outline_rounded, size: 16, color: Color(0xFF64748B)),
            label: Text(
              'How does AI matching work?',
              style: GoogleFonts.plusJakartaSans(color: const Color(0xFF64748B), fontSize: 13, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsList(VolunteerProvider provider) {
    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            boxShadow: [
              BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 4)),
            ],
          ],
          child: Row(
            children: [
              const Icon(Icons.auto_awesome_rounded, size: 14, color: Color(0xFF00BFA5)),
              const SizedBox(width: 12),
              Text(
                'FOUND ${provider.matchResults.length} OPTIMAL DEPLOYMENTS',
                style: GoogleFonts.plusJakartaSans(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  fontSize: 10,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
            itemCount: provider.matchResults.length,
            itemBuilder: (context, index) {
              return MatchResultCard(match: provider.matchResults[index]);
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(24.0),
          child: ElevatedButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Notifications dispatched to ${provider.matchResults.length} responders'),
                  behavior: SnackBarBehavior.floating,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  backgroundColor: const Color(0xFF0F172A),
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0F172A),
              minimumSize: const Size(double.infinity, 64),
            ),
            child: const Text('NOTIFY ALL RESPONDERS'),
          ),
        ),
      ],
    );
  }

  void _showMatchingExplanation(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.7,
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(40)),
          ),
          padding: const EdgeInsets.all(32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 32),
              Row(
                children: [
                  const Icon(Icons.auto_awesome_rounded, color: Color(0xFF00BFA5), size: 28),
                  const SizedBox(width: 16),
                  Text(
                    'Matching Algorithm',
                    style: GoogleFonts.plusJakartaSans(fontSize: 22, fontWeight: FontWeight.w900, color: const Color(0xFF0F172A), letterSpacing: -1),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              _buildExplanationItem('🎯', 'Skill Matrix', 'Gemini compares volunteer competencies with the core mission requirements.'),
              _buildExplanationItem('📍', 'Geospatial Proximity', 'Optimization based on real-time distance and estimated response time.'),
              _buildExplanationItem('🔥', 'Urgency Priority', 'High-severity missions are automatically assigned to the most senior responders.'),
              _buildExplanationItem('⭐', 'Confidence Score', 'Probability of successful mission completion based on past responder data.'),
              const Spacer(),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('UNDERSTOOD'),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildExplanationItem(String emoji, String title, String description) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: const Color(0xFFF8FAFC), borderRadius: BorderRadius.circular(16)),
            child: Text(emoji, style: const TextStyle(fontSize: 20)),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800, fontSize: 15, color: const Color(0xFF0F172A))),
                const SizedBox(height: 4),
                Text(description, style: GoogleFonts.plusJakartaSans(color: const Color(0xFF64748B), fontSize: 13, height: 1.5, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
