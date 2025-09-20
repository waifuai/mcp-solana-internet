"""
Manim animation for visualizing the Solana Payment System with MCP integration.

This script creates an animated visualization that demonstrates:
- The complete architecture of the MCP Solana Internet payment system
- Step-by-step payment processing flow from user request to blockchain confirmation
- Integration between Flask payment API, MCP server, and Solana blockchain
- Visual representation of transaction creation and validation processes

The animation includes:
- System architecture overview with all components
- Detailed payment flow with code snippets
- Complete end-to-end transaction visualization
- Success confirmation and system integration display

Usage:
    manim solana_payment_animation.py SolanaPaymentAnimation
    # or for higher quality:
    manim -pqh solana_payment_animation.py SolanaPaymentAnimation

Requirements:
- Manim Community installed (pip install manim)
- Python 3.7+
- Output generated in media/videos/ directory
"""
from manim import *
import numpy as np

class SolanaPaymentAnimation(Scene):
    def construct(self):
        # Set up colors
        solana_orange = "#9945FF"
        solana_green = "#14F195"
        background_blue = "#0A0E27"
        text_white = "#FFFFFF"
        accent_purple = "#8B5CF6"

        # Background
        self.camera.background_color = background_blue

        # Title
        title = Text("Solana Payment System", font_size=48, color=text_white)
        subtitle = Text("MCP-Integrated Payment Processing", font_size=24, color=solana_green)
        subtitle.next_to(title, DOWN)

        title_group = VGroup(title, subtitle).move_to(UP * 2)
        self.play(Write(title_group))
        self.wait(2)

        # Clear screen for detailed flow
        self.play(FadeOut(title_group))
        self.wait(1)
        
        # System Architecture Overview
        self.show_architecture(solana_orange, solana_green, text_white, accent_purple)
        self.wait(3)

        # Detailed Payment Flow
        self.show_payment_flow(solana_orange, solana_green, text_white, accent_purple)

    def show_architecture(self, solana_orange, solana_green, text_white, accent_purple):
        """Show the overall system architecture"""

        # Create component boxes
        config_box = Rectangle(width=2, height=1, color=solana_orange, fill_opacity=0.2)
        config_text = Text("config.py", font_size=16, color=text_white)
        config_group = VGroup(config_box, config_text).move_to(LEFT * 4 + UP * 1.5)

        payments_box = Rectangle(width=2.5, height=1, color=solana_green, fill_opacity=0.2)
        payments_text = Text("payments.py", font_size=16, color=text_white)
        payments_group = VGroup(payments_box, payments_text).move_to(LEFT * 1 + UP * 1.5)

        server_box = Rectangle(width=2, height=1, color=accent_purple, fill_opacity=0.2)
        server_text = Text("server.py", font_size=16, color=text_white)
        server_group = VGroup(server_box, server_text).move_to(RIGHT * 2 + UP * 1.5)

        # Solana blockchain
        solana_box = Rectangle(width=3, height=1.5, color=solana_orange, fill_opacity=0.3)
        solana_text = Text("Solana\nBlockchain", font_size=18, color=text_white)
        solana_group = VGroup(solana_box, solana_text).move_to(DOWN * 1.5)

        # User
        user_circle = Circle(radius=0.5, color=text_white)
        user_text = Text("User", font_size=16, color=text_white)
        user_group = VGroup(user_circle, user_text).move_to(LEFT * 4 + DOWN * 1.5)

        # Arrows
        arrow1 = Arrow(config_group.get_bottom(), payments_group.get_left(), color=solana_green)
        arrow2 = Arrow(payments_group.get_right(), server_group.get_left(), color=accent_purple)
        arrow3 = Arrow(server_group.get_bottom(), solana_group.get_top(), color=solana_orange)
        arrow4 = Arrow(user_group.get_right(), config_group.get_left(), color=text_white)

        # Labels
        label1 = Text("Configuration", font_size=12, color=solana_green).next_to(arrow1, UP)
        label2 = Text("Payment API", font_size=12, color=accent_purple).next_to(arrow2, UP)
        label3 = Text("Blockchain\nInteraction", font_size=12, color=solana_orange).next_to(arrow3, RIGHT)
        label4 = Text("User Request", font_size=12, color=text_white).next_to(arrow4, UP)

        # Animate
        components = [config_group, payments_group, server_group, solana_group, user_group]
        arrows = [arrow1, arrow2, arrow3, arrow4]
        labels = [label1, label2, label3, label4]

        for i, component in enumerate(components):
            self.play(Create(component), run_time=0.5)
            if i < len(arrows):
                self.play(Create(arrows[i]), run_time=0.3)
                self.play(Write(labels[i]), run_time=0.3)

        self.wait(2)

        # Highlight the flow
        flow_text = Text("Complete Payment Flow", font_size=20, color=solana_green)
        flow_text.move_to(DOWN * 3)
        self.play(Write(flow_text))

        # Flow animation
        flow_arrows = VGroup(arrow4, arrow1, arrow2, arrow3)
        self.play(flow_arrows.animate.set_color(solana_green), run_time=2)
        self.play(flow_arrows.animate.set_color(text_white), run_time=0.5)

        self.play(FadeOut(flow_text))
        self.remove(flow_text)

        # Clean up all architecture objects before returning
        all_objects = [config_group, payments_group, server_group, solana_group, user_group] + arrows + labels
        self.play(FadeOut(VGroup(*all_objects)))
        self.remove(*all_objects)

    def show_payment_flow(self, solana_orange, solana_green, text_white, accent_purple):
        """Show detailed payment processing flow"""

        # Step 1: Configuration Loading
        step1_title = Text("Step 1: Configuration Loading", font_size=24, color=solana_orange)
        step1_title.move_to(UP * 3)

        config_code = Code(
            code="""
# config.py
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "http://localhost:8899")
PAYMENT_WALLET = Keypair.from_seed(seed_bytes)
LAMPORTS_PER_SOL = 10**9
            """,
            language="python",
            font_size=16,
            background="rectangle"
        ).scale(0.7).next_to(step1_title, DOWN)

        self.play(Write(step1_title))
        self.play(Create(config_code))
        self.wait(2)

        # Clear step 1
        self.play(FadeOut(step1_title), FadeOut(config_code))
        self.remove(step1_title, config_code)

        # Step 2: Payment Request
        step2_title = Text("Step 2: Payment Request", font_size=24, color=solana_green)
        step2_title.move_to(UP * 3)

        payment_request = Code(
            code="""
# User sends payment request
POST /process_payment_action
{
    "amount_sol": 0.1,
    "resource_id": "premium_content"
}
            """,
            language="json",
            font_size=16,
            background="rectangle"
        ).scale(0.7).next_to(step2_title, DOWN)

        self.play(Write(step2_title))
        self.play(Create(payment_request))
        self.wait(2)

        # Clear step 2
        self.play(FadeOut(step2_title), FadeOut(payment_request))
        self.remove(step2_title, payment_request)

        # Step 3: Transaction Creation
        step3_title = Text("Step 3: Transaction Creation", font_size=24, color=accent_purple)
        step3_title.move_to(UP * 3)

        transaction_code = Code(
            code="""
# payments.py - Create Solana transaction
transfer_ix = transfer(
    TransferParams(
        from_pubkey=Pubkey.from_string(user_pubkey),
        to_pubkey=PAYMENT_WALLET.pubkey(),
        lamports=amount_lamports,
    )
)
            """,
            language="python",
            font_size=14,
            background="rectangle"
        ).scale(0.6).next_to(step3_title, DOWN)

        self.play(Write(step3_title))
        self.play(Create(transaction_code))
        self.wait(2)

        # Clear step 3
        self.play(FadeOut(step3_title), FadeOut(transaction_code))
        self.remove(step3_title, transaction_code)

        # Step 4: MCP Server Processing
        step4_title = Text("Step 4: MCP Server Processing", font_size=24, color=solana_orange)
        step4_title.move_to(UP * 3)

        mcp_code = Code(
            code="""
# server.py - Process payment
async def process_payment():
    # Validate transaction
    # Check payment amount
    # Record payment in system
    return f"Payment of {amount_sol:.6f} SOL received"
            """,
            language="python",
            font_size=14,
            background="rectangle"
        ).scale(0.6).next_to(step4_title, DOWN)

        self.play(Write(step4_title))
        self.play(Create(mcp_code))
        self.wait(2)

        # Clear step 4
        self.play(FadeOut(step4_title), FadeOut(mcp_code))
        self.remove(step4_title, mcp_code)

        # Step 5: Blockchain Confirmation
        step5_title = Text("Step 5: Blockchain Confirmation", font_size=24, color=solana_green)
        step5_title.move_to(UP * 3)

        blockchain_confirmation = Code(
            code="""
# Verify transaction on Solana
transaction_response = await client.post(
    RPC_ENDPOINT,
    json={
        "jsonrpc": "2.0",
        "method": "getTransaction",
        "params": [str(tx_signature), {"commitment": "confirmed"}]
    }
)
            """,
            language="python",
            font_size=14,
            background="rectangle"
        ).scale(0.6).next_to(step5_title, DOWN)

        self.play(Write(step5_title))
        self.play(Create(blockchain_confirmation))
        self.wait(2)

        # Clear step 5
        self.play(FadeOut(step5_title), FadeOut(blockchain_confirmation))
        self.remove(step5_title, blockchain_confirmation)

        success_text = Text("Payment Successful! ✅", font_size=36, color=solana_green)
        success_text.move_to(ORIGIN)

        checkmark = Text("✓", font_size=48, color=solana_green).next_to(success_text, LEFT)

        success_group = VGroup(checkmark, success_text)
        self.play(Write(success_group))
        self.wait(3)

        # Clean up success message before showing complete flow
        self.play(FadeOut(success_group))
        self.remove(success_group)

        # Show complete flow diagram
        self.show_complete_flow(solana_orange, solana_green, text_white, accent_purple)

    def show_complete_flow(self, solana_orange, solana_green, text_white, accent_purple):
        """Show the complete flow diagram"""

        flow_title = Text("Complete Payment Flow", font_size=28, color=text_white)
        flow_title.move_to(UP * 3.5)

        # Create flow steps
        steps = [
            "1. User requests access",
            "2. Check payment required",
            "3. Generate payment transaction",
            "4. User signs and submits transaction",
            "5. Validate transaction on blockchain",
            "6. Grant access to resource"
        ]

        step_texts = VGroup()
        for i, step in enumerate(steps):
            step_text = Text(step, font_size=16, color=text_white)
            step_text.move_to(LEFT * 4 + UP * (2 - i * 0.6))
            step_texts.add(step_text)

        # Flow arrows
        arrows = VGroup()
        for i in range(len(steps) - 1):
            start = LEFT * 4 + UP * (2 - i * 0.6) + RIGHT * 3
            end = LEFT * 4 + UP * (2 - (i + 1) * 0.6) + RIGHT * 1
            arrow = Arrow(start, end, color=solana_green, stroke_width=3)
            arrows.add(arrow)

        # Key components
        components = VGroup(
            Text("Frontend\n(DApp/Web)", font_size=14, color=accent_purple).move_to(LEFT * 4 + DOWN * 1),
            Text("MCP Server\n(server.py)", font_size=14, color=solana_orange).move_to(RIGHT * 2 + DOWN * 1),
            Text("Payment API\n(payments.py)", font_size=14, color=solana_green).move_to(RIGHT * 4 + DOWN * 1),
            Text("Solana\nBlockchain", font_size=14, color=solana_orange).move_to(RIGHT * 2 + DOWN * 2.5)
        )

        # Animate
        self.play(Write(flow_title))
        self.play(Write(step_texts))
        self.play(Create(arrows))
        self.play(Write(components))

        # Highlight the flow
        self.play(arrows.animate.set_color(solana_orange), run_time=2)
        self.play(arrows.animate.set_color(solana_green), run_time=0.5)

        self.wait(3)

        # Clear flow diagram
        self.play(FadeOut(flow_title), FadeOut(step_texts), FadeOut(arrows), FadeOut(components))
        self.remove(flow_title, step_texts, arrows, components)

        # Final message
        final_message = Text(
            "Solana Payment System with MCP Integration\nReady for production use!",
            font_size=20,
            color=text_white
        )
        final_message.move_to(DOWN * 3.5)

        self.play(Write(final_message))
        self.wait(2)

        # Clear final message
        self.play(FadeOut(final_message))
        self.remove(final_message)

if __name__ == "__main__":
    # This will render the animation
    # Run with: manim solana_payment_animation.py SolanaPaymentAnimation
    pass